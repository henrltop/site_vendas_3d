from decimal import Decimal
from catalog.models import Product
from django.utils import timezone
from .models import UserCart

class Cart:
    def __init__(self, request):
        self.request = request
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}

        # Normaliza imediatamente para remover Decimals residuais de sessões antigas
        self.cart = self._normalize_cart_dict(cart)
        self.session['cart'] = self.cart
        self.session.modified = True
        self.coupon_id = self.session.get('coupon_id')
        self.user_cart = None

        if request.user.is_authenticated:
            self.user_cart, _ = UserCart.objects.get_or_create(user=request.user)
            self._sync_authenticated_cart()

    def _merge_carts(self, session_cart, db_cart):
        merged = self._normalize_cart_dict(db_cart or {})

        for item_id, session_item in (session_cart or {}).items():
            if item_id in merged:
                # Evita dobrar quantidades: mantém o maior valor (permite extras adicionados antes de logar)
                merged_qty = int(merged[item_id].get('quantity', 0))
                session_qty = int(session_item.get('quantity', 0))
                merged[item_id]['quantity'] = max(merged_qty, session_qty)
            else:
                merged[item_id] = self._normalize_item(session_item)

        return merged

    def _sync_authenticated_cart(self):
        merged_user_id = self.session.get('cart_merged_user_id')
        db_cart = self.user_cart.data or {}

        if merged_user_id != self.request.user.id:
            final_cart = self._merge_carts(self.cart, db_cart)
            self.session['cart_merged_user_id'] = self.request.user.id
        else:
            final_cart = db_cart

        final_cart = self._normalize_cart_dict(final_cart)
        self.cart = final_cart
        self.session['cart'] = final_cart

        if self.user_cart.coupon_id:
            self.coupon_id = self.user_cart.coupon_id
            self.session['coupon_id'] = self.user_cart.coupon_id

        self.user_cart.data = final_cart
        self.user_cart.coupon_id = self.coupon_id
        self.user_cart.save(update_fields=['data', 'coupon_id', 'updated_at'])

        self.session.modified = True

    def add(self, product, quantity=1, color=None, custom_fields=None, override_quantity=False):
        # Criar chave única baseada em cores e custom fields para separar variações iguais no carrinho
        custom_fields_str = ""
        if custom_fields:
            for k in sorted(custom_fields.keys()):
                custom_fields_str += f"{k}:{custom_fields[k]}_"
        
        item_id = f"{product.id}_{color or 'None'}_{custom_fields_str}"
        
        if item_id not in self.cart:
            self.cart[item_id] = {
                'product_id': product.id,
                'quantity': 0,
                'color': color,
                'custom_fields': custom_fields or {},
                'price': str(product.base_price)
            }
        
        if override_quantity:
            self.cart[item_id]['quantity'] = int(quantity)
        else:
            self.cart[item_id]['quantity'] += int(quantity)
            
        self.save()

    def update(self, item_id, quantity):
        if item_id in self.cart:
            qty = int(quantity)
            if qty <= 0:
                self.remove(item_id)
            else:
                self.cart[item_id]['quantity'] = qty
                self.save()

    def remove(self, item_id):
        if item_id in self.cart:
            del self.cart[item_id]
            self.save()

    def save(self):
        # Normaliza antes de persistir para evitar problemas com JSON serializer em sessão/JSONField
        self.cart = self._normalize_cart_dict(self.cart)
        self.session['cart'] = self.cart
        self.session['coupon_id'] = self.coupon_id

        if self.request.user.is_authenticated and self.user_cart is not None:
            self.user_cart.data = self.cart
            self.user_cart.coupon_id = self.coupon_id
            self.user_cart.save(update_fields=['data', 'coupon_id', 'updated_at'])

        self.session.modified = True

    def set_coupon(self, coupon):
        self.session['coupon_id'] = coupon.id
        self.coupon_id = coupon.id
        self.save()

    def remove_coupon(self):
        if 'coupon_id' in self.session:
            del self.session['coupon_id']
        self.coupon_id = None
        self.save()

    def get_coupon(self):
        if not self.coupon_id:
            return None
        try:
            from orders.models import Coupon  # import local to avoid circular import at module load
            coupon = Coupon.objects.select_related('category').get(id=self.coupon_id)
        except Coupon.DoesNotExist:
            self.remove_coupon()
            return None

        if not coupon.is_valid(timezone.now()):
            self.remove_coupon()
            return None

        return coupon

    def __iter__(self):
        product_ids = [item['product_id'] for item in self.cart.values()]
        products = Product.objects.filter(id__in=product_ids)
        product_map = {product.id: product for product in products}
        
        for item_id, item_data in self.cart.items():
            product = product_map.get(item_data['product_id'])
            if product is None:
                continue # produto foi deletado

            # Copiamos os dados do item antes de enriquecer para não mutar a sessão.
            item = item_data.copy()
            item['product'] = product
            item['id'] = item_id
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())
        
    def get_total_items(self):
        return sum(item['quantity'] for item in self.cart.values())

    def __len__(self):
        return self.get_total_items()

    def get_discount(self):
        coupon = self.get_coupon()
        if not coupon:
            return Decimal('0')

        discountable_total = Decimal('0')
        for item in self:
            product_category_id = item['product'].category_id if item['product'].category else None
            if (coupon.category is None) or (coupon.category_id == product_category_id):
                discountable_total += item['total_price']

        discount = discountable_total * Decimal(coupon.discount_percent) / Decimal('100')
        return discount.quantize(Decimal('0.01'))

    def get_total_after_discount(self):
        total = Decimal(self.get_total_price())
        discount = self.get_discount()
        result = total - discount
        return result if result > 0 else Decimal('0.00')

    def clear(self):
        self.session['cart'] = {}
        self.cart = {}
        self.save()

    # --- Helpers ---
    def _normalize_item(self, item_data):
        item = item_data or {}
        price_raw = item.get('price', '0')

        # Converte Decimals (ou outros números) para string; Django JSON serializer não aceita Decimal
        if isinstance(price_raw, Decimal):
            price = str(price_raw)
        else:
            price = str(price_raw)

        return {
            'product_id': item.get('product_id'),
            'quantity': int(item.get('quantity', 0)),
            'color': item.get('color'),
            'custom_fields': item.get('custom_fields') or {},
            'price': price,
        }

    def _normalize_cart_dict(self, cart_data):
        return {item_id: self._normalize_item(data) for item_id, data in (cart_data or {}).items() if isinstance(data, dict)}
