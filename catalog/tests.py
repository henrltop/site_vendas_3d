from django.test import TestCase
from decimal import Decimal
from catalog.models import Category, Product

class CatalogTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Decoração', slug='decoracao')
        self.product = Product.objects.create(
            category=self.category,
            name='Vaso Espiral',
            slug='vaso-espiral',
            short_description='Vaso 3D espiral',
            description='Ótimo para sala.',
            base_price=Decimal('45.00')
        )

    def test_product_creation(self):
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(self.product.name, 'Vaso Espiral')
        self.assertEqual(self.product.base_price, Decimal('45.00'))

    def test_product_list_view(self):
        response = self.client.get('/produtos/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vaso Espiral')
