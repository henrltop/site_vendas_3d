from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import OrderDraft, Coupon
from .forms import CouponForm
from catalog.forms import ProductForm, CategoryForm
from catalog.models import Product, Category, ProductImage, ProductColor, ProductCustomField


def _save_product_relations(request, product):
    """Process images, colors and custom fields from a POST request."""

    # ── IMAGES ──────────────────────────────────────────────────────────────
    for img_id in request.POST.getlist('delete_image'):
        ProductImage.objects.filter(product=product, pk=img_id).delete()

    for img_file in request.FILES.getlist('new_images'):
        ProductImage.objects.create(
            product=product, image=img_file,
            alt_text=product.name, order=0,
        )

    # ── COLORS ──────────────────────────────────────────────────────────────
    delete_colors = set(request.POST.getlist('delete_color'))
    for color in list(product.colors.all()):
        if str(color.pk) in delete_colors:
            color.delete()
            continue
        name = request.POST.get(f'color_name_{color.pk}', '').strip()
        hex_val = request.POST.get(f'color_hex_{color.pk}', '').strip()
        if name:
            color.name = name
            color.hex_optional = hex_val
            color.save()

    for name, hex_val in zip(
        request.POST.getlist('new_color_name'),
        request.POST.getlist('new_color_hex'),
    ):
        if name.strip():
            ProductColor.objects.create(
                product=product, name=name.strip(), hex_optional=hex_val.strip()
            )

    # ── CUSTOM FIELDS ────────────────────────────────────────────────────────
    delete_fields = set(request.POST.getlist('delete_field'))
    for field in list(product.custom_fields.all()):
        if str(field.pk) in delete_fields:
            field.delete()
            continue
        label = request.POST.get(f'field_label_{field.pk}', '').strip()
        if label:
            field.label = label
            field.field_type = request.POST.get(f'field_type_{field.pk}', 'text')
            field.required = request.POST.get(f'field_required_{field.pk}') == '1'
            field.options_json = request.POST.get(f'field_options_{field.pk}', '')
            field.save()

    new_labels = request.POST.getlist('new_field_label')
    new_types = request.POST.getlist('new_field_type')
    new_requireds = request.POST.getlist('new_field_required')
    new_options = request.POST.getlist('new_field_options')
    for i, label in enumerate(new_labels):
        label = label.strip()
        if label:
            ProductCustomField.objects.create(
                product=product,
                label=label,
                field_type=new_types[i] if i < len(new_types) else 'text',
                required=new_requireds[i] == '1' if i < len(new_requireds) else False,
                options_json=new_options[i] if i < len(new_options) else '',
            )


# ─── DASHBOARD ────────────────────────────────────────────────────────────────

@staff_member_required
def dashboard(request):
    today = timezone.now().date()
    orders_today = OrderDraft.objects.filter(created_at__date=today).count()
    total_revenue = OrderDraft.objects.aggregate(t=Sum('total_after_discount'))['t'] or 0
    active_products = Product.objects.filter(is_active=True).count()
    active_coupons = Coupon.objects.filter(active=True).count()
    recent_orders = OrderDraft.objects.select_related('coupon').order_by('-created_at')[:15]
    return render(request, 'admin/custom_dashboard.html', {
        'orders_today': orders_today,
        'total_revenue': total_revenue,
        'active_products': active_products,
        'active_coupons': active_coupons,
        'recent_orders': recent_orders,
    })


# ─── PRODUCTS ────────────────────────────────────────────────────────────────

@staff_member_required
def product_list(request):
    qs = Product.objects.select_related('category').prefetch_related('images').order_by('-created_at')
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(name__icontains=q)
    return render(request, 'admin/products/list.html', {'products': qs, 'q': q})


@staff_member_required
def product_create(request):
    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        product = form.save()
        _save_product_relations(request, product)
        messages.success(request, f"Produto «{product.name}» criado!")
        return redirect('custom_admin:product_edit', pk=product.pk)
    return render(request, 'admin/products/form.html', {'form': form, 'product': None})


@staff_member_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == 'POST' and form.is_valid():
        product = form.save()
        _save_product_relations(request, product)
        messages.success(request, f"Produto «{product.name}» atualizado!")
        return redirect('custom_admin:product_edit', pk=product.pk)
    return render(request, 'admin/products/form.html', {
        'form': form,
        'product': product,
        'images': product.images.all(),
        'colors': product.colors.all(),
        'custom_fields': product.custom_fields.all(),
    })


@staff_member_required
@require_POST
def product_toggle_active(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.is_active = not product.is_active
    product.save(update_fields=['is_active'])
    messages.info(request, f"Produto «{product.name}» {'ativado' if product.is_active else 'desativado'}.")
    return redirect('custom_admin:product_list')


@staff_member_required
@require_POST
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    name = product.name
    product.delete()
    messages.success(request, f"Produto «{name}» excluído.")
    return redirect('custom_admin:product_list')


# ─── ORDERS ──────────────────────────────────────────────────────────────────

@staff_member_required
def order_list(request):
    qs = OrderDraft.objects.select_related('coupon').order_by('-created_at')
    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        qs = qs.filter(status=status_filter)
    return render(request, 'admin/orders/list.html', {
        'orders': qs,
        'status_filter': status_filter,
        'status_choices': OrderDraft.STATUS_CHOICES,
    })


@staff_member_required
def order_detail(request, pk):
    order = get_object_or_404(OrderDraft, pk=pk)
    return render(request, 'admin/orders/detail.html', {'order': order})


@staff_member_required
@require_POST
def order_update_status(request, pk):
    order = get_object_or_404(OrderDraft, pk=pk)
    new_status = request.POST.get('status')
    valid = [s[0] for s in OrderDraft.STATUS_CHOICES]
    if new_status in valid:
        order.status = new_status
        order.save(update_fields=['status'])
        messages.success(request, f"Status do pedido #{order.id} atualizado.")
    return redirect('custom_admin:order_detail', pk=pk)


# ─── COUPONS ─────────────────────────────────────────────────────────────────

@staff_member_required
def coupon_list(request):
    coupons = Coupon.objects.select_related('category').order_by('-valid_from')
    return render(request, 'admin/coupons/list.html', {'coupons': coupons})


@staff_member_required
def coupon_create(request):
    form = CouponForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        coupon = form.save()
        messages.success(request, f"Cupom «{coupon.code}» criado!")
        return redirect('custom_admin:coupon_list')
    return render(request, 'admin/coupons/form.html', {'form': form, 'coupon': None})


@staff_member_required
def coupon_edit(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)
    form = CouponForm(request.POST or None, instance=coupon)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f"Cupom «{coupon.code}» atualizado!")
        return redirect('custom_admin:coupon_list')
    return render(request, 'admin/coupons/form.html', {'form': form, 'coupon': coupon})


@staff_member_required
@require_POST
def coupon_toggle_active(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)
    coupon.active = not coupon.active
    coupon.save(update_fields=['active'])
    messages.info(request, f"Cupom {coupon.code} agora {'ativo' if coupon.active else 'inativo'}.")
    return redirect('custom_admin:coupon_list')


@staff_member_required
@require_POST
def coupon_delete(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)
    code = coupon.code
    coupon.delete()
    messages.success(request, f"Cupom «{code}» excluído.")
    return redirect('custom_admin:coupon_list')


# ─── CATEGORIES ──────────────────────────────────────────────────────────────

@staff_member_required
def category_list(request):
    categories = Category.objects.annotate(product_count=Count('products')).order_by('name')
    return render(request, 'admin/categories/list.html', {'categories': categories})


@staff_member_required
def category_create(request):
    form = CategoryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cat = form.save()
        messages.success(request, f"Categoria «{cat.name}» criada!")
        return redirect('custom_admin:category_list')
    return render(request, 'admin/categories/form.html', {'form': form, 'category': None})


@staff_member_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, instance=category)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f"Categoria «{category.name}» atualizada!")
        return redirect('custom_admin:category_list')
    return render(request, 'admin/categories/form.html', {'form': form, 'category': category})


@staff_member_required
@require_POST
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    name = category.name
    category.delete()
    messages.success(request, f"Categoria «{name}» excluída.")
    return redirect('custom_admin:category_list')
