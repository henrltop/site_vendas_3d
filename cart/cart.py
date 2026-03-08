from decimal import Decimal
from catalog.models import Product
from django.utils import timezone

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart
        self.coupon_id = self.session.get('coupon_id')

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
        
        cart_copy = self.cart.copy()
        
        # Mapeando instâncias de produto de volta aos itens
        for product in products:
            for item_id, item_data in cart_copy.items():
                if item_data['product_id'] == product.id:
                    item_data['product'] = product
                    
        for item_id, item in cart_copy.items():
            if 'product' not in item:
                continue # produto foi deletado
                
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
        del self.session['cart']
        self.save()
