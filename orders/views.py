from django.shortcuts import render, redirect
from cart.cart import Cart
from .models import OrderDraft
from .whatsapp_service import generate_whatsapp_link

def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect('cart:cart_detail')
        
    if request.method == 'POST':
        customer_name = request.POST.get('customer_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        delivery_option = request.POST.get('delivery_option', '')
        notes = request.POST.get('notes', '')

        if not customer_name or not phone or not address:
            return render(request, 'orders/checkout.html', {
                'cart': cart,
                'error': 'Por favor, preencha nome, telefone e endereço.',
                'form_data': request.POST,
            })

        coupon = cart.get_coupon()
        discount_amount = cart.get_discount()
        total_after_discount = cart.get_total_after_discount()
        
        items_json = {}
        for item in cart:
            items_json[item['id']] = {
                'product_id': item['product'].id,
                'product_name': item['product'].name,
                'quantity': item['quantity'],
                'color': item['color'],
                'custom_fields': item['custom_fields'],
                'price': str(item['price']),
            }
            
        draft = OrderDraft.objects.create(
            user=request.user if request.user.is_authenticated else None,
            customer_name=customer_name,
            phone=phone,
            email=email,
            address=address,
            city=city,
            delivery_option=delivery_option,
            notes=notes,
            items_json=items_json,
            coupon=coupon,
            discount_amount=discount_amount,
            total_estimated=cart.get_total_price(),
            total_after_discount=total_after_discount,
            status='enviado_whatsapp'
        )

        if coupon:
            coupon.usage_count += 1
            coupon.save(update_fields=['usage_count'])
        
        # Link do whatsapp
        link = generate_whatsapp_link(draft)
        
        # Limpar carrinho
        cart.clear()
        
        return render(request, 'orders/checkout_success.html', {'whatsapp_link': link, 'order': draft})

    return render(request, 'orders/checkout.html', {'cart': cart})
