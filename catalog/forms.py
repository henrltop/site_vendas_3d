from django import forms
from .models import Product, Tag, Category, ProductImage


class ProductForm(forms.ModelForm):
    tags_csv = forms.CharField(
        label="Tags (#)", required=False,
        help_text="Separe por vírgula. Ex: articulado,animal,decoração"
    )
    image = forms.ImageField(label="Imagem principal (opcional)", required=False)

    class Meta:
        model = Product
        fields = [
            'name', 'slug', 'category', 'short_description', 'description',
            'base_price', 'lead_time_text', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def save(self, commit=True):
        tags_csv = self.cleaned_data.pop('tags_csv', '')
        image_file = self.cleaned_data.pop('image', None)
        product = super().save(commit)

        # Tags
        if commit:
            tags = []
            for raw in tags_csv.split(','):
                name = raw.strip()
                if not name:
                    continue
                slug = name.lower().replace(' ', '-')
                tag, _ = Tag.objects.get_or_create(slug=slug, defaults={'name': name})
                tags.append(tag)
            if tags:
                product.tags.set(tags)

            # Imagem principal
            if image_file:
                ProductImage.objects.create(product=product, image=image_file, alt_text=product.name, order=0)

        return product
