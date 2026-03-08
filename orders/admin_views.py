from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponseNotAllowed
from .models import OrderDraft, Coupon
from .forms import CouponForm
from catalog.forms import ProductForm
from catalog.models import Product


@staff_member_required
def dashboard(request):
    recent_orders = OrderDraft.objects.order_by('-created_at')[:10]
    coupons = Coupon.objects.order_by('-valid_from')[:10]
    return render(request, 'admin/custom_dashboard.html', {
        'recent_orders': recent_orders,
        'coupons': coupons,
    })


@staff_member_required
def coupon_create(request):
    form = CouponForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Cupom criado com sucesso!')
        return redirect('custom_admin:dashboard')
    return render(request, 'admin/coupon_form.html', {'form': form})


@staff_member_required
def coupon_toggle_active(request, pk):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    coupon = get_object_or_404(Coupon, pk=pk)
    coupon.active = not coupon.active
    coupon.save(update_fields=['active'])
    messages.info(request, f"Cupom {coupon.code} agora está {'ativo' if coupon.active else 'inativo'}.")
    return redirect('custom_admin:dashboard')


@staff_member_required
def product_create(request):
    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        product = form.save()
        messages.success(request, f"Produto '{product.name}' criado!")
        return redirect('custom_admin:dashboard')

    return render(request, 'admin/product_form.html', {'form': form})
