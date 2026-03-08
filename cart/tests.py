from django.test import TestCase, RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from catalog.models import Product
from decimal import Decimal
from cart.cart import Cart

class CartTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            short_description='desc',
            description='long desc',
            base_price=Decimal('10.00')
        )

    def test_add_to_cart(self):
        request = self.factory.get('/')
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        
        cart = Cart(request)
        self.assertEqual(len(list(cart)), 0)
        
        cart.add(product=self.product, quantity=2, color='Azul', custom_fields={'Nome': 'Ana'})
        self.assertEqual(len(list(cart)), 1)
        self.assertEqual(cart.get_total_items(), 2)
        self.assertEqual(cart.get_total_price(), Decimal('20.00'))
