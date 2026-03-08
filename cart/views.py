from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from catalog.models import Product
from orders.models import Coupon
from .cart import Cart

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    
    quantity = int(request.POST.get('quantity', 1))
    color = request.POST.get('color', '')
    
    custom_fields = {}
    for key, value in request.POST.items():
        if key.startswith('custom_') and value.strip():
            field_name = key.replace('custom_', '')
            custom_fields[field_name] = value.strip()
            
    cart.add(product=product, quantity=quantity, color=color, custom_fields=custom_fields)
    
    return redirect('cart:cart_detail')

def cart_remove(request, item_id):
    cart = Cart(request)
    cart.remove(item_id)
    return redirect('cart:cart_detail')

@require_POST
def cart_update(request, item_id):
    cart = Cart(request)
    quantity = int(request.POST.get('quantity', 1))
    cart.update(item_id, quantity)
    return redirect('cart:cart_detail')

def cart_detail(request):
    return render(request, 'cart/cart_detail.html')


@require_POST
def apply_coupon(request):
    cart = Cart(request)
    code = request.POST.get('coupon_code', '').strip()

    if not code:
        cart.remove_coupon()
        messages.info(request, 'Cupom removido.')
        return redirect('cart:cart_detail')

    try:
        coupon = Coupon.objects.select_related('category').get(code__iexact=code)
    except Coupon.DoesNotExist:
        messages.error(request, 'Cupom não encontrado.')
        return redirect('cart:cart_detail')

    if not coupon.is_valid():
        messages.error(request, 'Cupom expirado, inativo ou sem saldo de uso.')
        return redirect('cart:cart_detail')

    cart.set_coupon(coupon)
    messages.success(request, f"Cupom '{coupon.code}' aplicado com {coupon.discount_percent}% de desconto.")
    return redirect('cart:cart_detail')
