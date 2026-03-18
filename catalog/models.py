import io
import os

from django.db import models
from django.urls import reverse
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from PIL import Image as PILImage


class Tag(models.Model):
    name = models.CharField(max_length=80, unique=True, verbose_name="Nome da Tag")
    slug = models.SlugField(max_length=80, unique=True)

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ['name']

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=150, verbose_name="Nome da Categoria")
    slug = models.SlugField(max_length=150, unique=True)
    description = models.TextField(blank=True, verbose_name="Descrição")

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('catalog:category_detail', kwargs={'slug': self.slug})


class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Categoria")
    name = models.CharField(max_length=200, verbose_name="Nome do Produto")
    slug = models.SlugField(max_length=200, unique=True)
    short_description = models.CharField(max_length=255, verbose_name="Descrição Curta")
    description = models.TextField(verbose_name="Descrição Longa")
    base_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço Base")
    is_active = models.BooleanField(default=True, verbose_name="Ativo?")
    lead_time_text = models.CharField(max_length=100, default="Produção em 3 a 5 dias úteis", verbose_name="Prazo Estimado")
    tags = models.ManyToManyField(Tag, related_name='products', blank=True, verbose_name="Tags (#)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('catalog:product_detail', kwargs={'slug': self.slug})


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/%Y/%m/%d', verbose_name="Imagem")
    alt_text = models.CharField(max_length=200, blank=True, verbose_name="Texto Alternativo (SEO)")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordem")

    class Meta:
        verbose_name = "Imagem do Produto"
        verbose_name_plural = "Imagens do Produto"
        ordering = ['order']

    def __str__(self):
        return f"Imagem de {self.product.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            self._convert_to_webp()

    def _convert_to_webp(self):
        name = self.image.name
        if not name or name.lower().endswith('.webp'):
            return
        try:
            with default_storage.open(name, 'rb') as f:
                img = PILImage.open(f)
                img.load()

            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGBA')
            else:
                img = img.convert('RGB')

            buffer = io.BytesIO()
            img.save(buffer, format='WEBP', quality=82, method=6)
            buffer.seek(0)

            webp_name = os.path.splitext(name)[0] + '.webp'
            default_storage.save(webp_name, ContentFile(buffer.read()))
            default_storage.delete(name)

            ProductImage.objects.filter(pk=self.pk).update(image=webp_name)
            self.image.name = webp_name
        except Exception:
            pass  # Keep original if conversion fails


class ProductColor(models.Model):
    product = models.ForeignKey(Product, related_name='colors', on_delete=models.CASCADE)
    name = models.CharField(max_length=100, verbose_name="Nome da Cor")
    hex_optional = models.CharField(max_length=7, blank=True, help_text="Ex: #FF0000", verbose_name="Código Hexadecimal")

    class Meta:
        verbose_name = "Cor Disponível"
        verbose_name_plural = "Cores Disponíveis"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.product.name})"


class ProductCustomField(models.Model):
    FIELD_TYPES = (
        ('text', 'Texto Simples'),
        ('number', 'Número'),
        ('select', 'Seleção (Dropdown)'),
    )

    product = models.ForeignKey(Product, related_name='custom_fields', on_delete=models.CASCADE)
    label = models.CharField(max_length=150, verbose_name="Rótulo do Campo (ex: Tamanho)")
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES, default='text', verbose_name="Tipo de Campo")
    required = models.BooleanField(default=False, verbose_name="Obrigatório?")
    options_json = models.TextField(blank=True, help_text="Se for 'Seleção', separe as opções por vírgula. Ex: P,M,G", verbose_name="Opções")

    class Meta:
        verbose_name = "Campo Personalizado"
        verbose_name_plural = "Campos Personalizados"
        ordering = ['id']

    def __str__(self):
        return f"{self.label} ({self.product.name})"

    def get_options_list(self):
        if self.field_type == 'select' and self.options_json:
            return [opt.strip() for opt in self.options_json.split(',') if opt.strip()]
        return []
