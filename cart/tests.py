from django.test import TestCase, RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from catalog.models import Product
from decimal import Decimal
from cart.cart import Cart
from cart.models import UserCart

class CartTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.User = get_user_model()
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            short_description='desc',
            description='long desc',
            base_price=Decimal('10.00')
        )

    def _get_request(self, session_cart=None, user=None):
        request = self.factory.get('/')
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        if session_cart is not None:
            request.session['cart'] = session_cart
        request.session.save()
        request.user = user if user else AnonymousUser()
        return request

    def test_add_to_cart(self):
        request = self._get_request()
        cart = Cart(request)
        self.assertEqual(len(list(cart)), 0)
        
        cart.add(product=self.product, quantity=2, color='Azul', custom_fields={'Nome': 'Ana'})
        self.assertEqual(len(list(cart)), 1)
        self.assertEqual(cart.get_total_items(), 2)
        self.assertEqual(cart.get_total_price(), Decimal('20.00'))

    def test_iter_does_not_mutate_session_cart_price_type(self):
        item_id = f"{self.product.id}_None_"
        request = self._get_request(session_cart={
            item_id: {
                'product_id': self.product.id,
                'quantity': 1,
                'color': None,
                'custom_fields': {},
                'price': str(self.product.base_price),
            }
        })

        cart = Cart(request)
        items = list(cart)

        self.assertEqual(len(items), 1)
        self.assertIsInstance(items[0]['price'], Decimal)
        self.assertIsInstance(cart.cart[item_id]['price'], str)
        self.assertIsInstance(request.session['cart'][item_id]['price'], str)

    def test_merge_does_not_double_existing_items(self):
        user = self.User.objects.create_user(username='merge', password='x')
        item_id = f"{self.product.id}_None_"
        base_item = {
            'product_id': self.product.id,
            'quantity': 4,
            'color': None,
            'custom_fields': {},
            'price': str(self.product.base_price)
        }
        # User cart already has 4 units
        UserCart.objects.create(user=user, data={item_id: base_item})

        # Session cart mirrors same quantities (should not double to 8)
        request = self._get_request(session_cart={item_id: base_item}, user=user)
        cart = Cart(request)

        self.assertEqual(cart.cart[item_id]['quantity'], 4)

    def test_merge_keeps_extra_if_greater(self):
        user = self.User.objects.create_user(username='merge-extra', password='x')
        item_id = f"{self.product.id}_None_"
        db_item = {
            'product_id': self.product.id,
            'quantity': 4,
            'color': None,
            'custom_fields': {},
            'price': str(self.product.base_price)
        }
        session_item = {
            'product_id': self.product.id,
            'quantity': 5,
            'color': None,
            'custom_fields': {},
            'price': str(self.product.base_price)
        }
        UserCart.objects.create(user=user, data={item_id: db_item})

        request = self._get_request(session_cart={item_id: session_item}, user=user)
        cart = Cart(request)

        self.assertEqual(cart.cart[item_id]['quantity'], 5)
