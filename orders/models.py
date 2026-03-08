from django.db import models
from django.conf import settings
from django.utils import timezone


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Código do Cupom")
    category = models.ForeignKey(
        'catalog.Category',
        related_name='coupons',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Categoria Alvo (opcional)"
    )
    discount_percent = models.PositiveIntegerField(verbose_name="Desconto (%)")
    valid_from = models.DateTimeField(verbose_name="Válido a partir de")
    valid_to = models.DateTimeField(verbose_name="Válido até")
    active = models.BooleanField(default=True, verbose_name="Ativo?")
    max_uses = models.PositiveIntegerField(null=True, blank=True, verbose_name="Limite de usos (opcional)")
    usage_count = models.PositiveIntegerField(default=0, verbose_name="Usos realizados")

    class Meta:
        verbose_name = "Cupom de Desconto"
        verbose_name_plural = "Cupons de Desconto"
        ordering = ['-valid_from']

    def __str__(self):
        target = self.category.name if self.category else "todas categorias"
        return f"{self.code} ({self.discount_percent}% em {target})"

    def is_valid(self, now=None):
        now = now or timezone.now()
        within_dates = self.valid_from <= now <= self.valid_to
        under_limit = (self.max_uses is None) or (self.usage_count < self.max_uses)
        return self.active and within_dates and under_limit

class OrderDraft(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Rascunho'),
        ('enviado_whatsapp', 'Enviado pro WhatsApp'),
        ('cancelado', 'Cancelado'),
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='order_drafts', verbose_name="Usuário")
    customer_name = models.CharField(max_length=150, verbose_name="Nome do Cliente")
    city = models.CharField(max_length=100, blank=True, verbose_name="Cidade")
    delivery_option = models.CharField(max_length=100, blank=True, verbose_name="Forma de Entrega/Retirada")
    notes = models.TextField(blank=True, verbose_name="Observações")
    
    items_json = models.JSONField(verbose_name="Itens do Pedido (Snapshot)", default=dict)
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL, related_name='orders', verbose_name="Cupom aplicado")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Total de desconto")
    total_estimated = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total Estimado")
    total_after_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Total após desconto")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="Status")

    class Meta:
        verbose_name = "Rascunho de Pedido"
        verbose_name_plural = "Rascunhos de Pedidos"
        ordering = ['-created_at']

    def __str__(self):
        return f"Pedido #{self.id} - {self.customer_name}"
