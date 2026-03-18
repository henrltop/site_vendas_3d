from django import forms
from django.utils.text import slugify
from .models import Product, Tag, Category, ProductImage


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'slug', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_slug(self):
        slug = self.cleaned_data.get('slug') or slugify(self.cleaned_data.get('name', ''))
        return slug


class ProductForm(forms.ModelForm):
    tags_csv = forms.CharField(
        label="Tags (#)", required=False,
        help_text="Separe por vírgula. Ex: articulado,animal,decoração"
    )

    class Meta:
        model = Product
        fields = [
            'name', 'slug', 'category', 'short_description', 'description',
            'base_price', 'lead_time_text', 'is_active',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['tags_csv'].initial = ', '.join(t.name for t in self.instance.tags.all())

    def save(self, commit=True):
        tags_csv = self.cleaned_data.get('tags_csv', '')
        product = super().save(commit=commit)

        if commit:
            tags = []
            for raw in tags_csv.split(','):
                name = raw.strip()
                if not name:
                    continue
                slug = slugify(name)
                tag, _ = Tag.objects.get_or_create(slug=slug, defaults={'name': name})
                tags.append(tag)
            product.tags.set(tags)

        return product
