from django.urls import path
from . import admin_views

app_name = 'custom_admin'

urlpatterns = [
    # Dashboard
    path('', admin_views.dashboard, name='dashboard'),

    # Products
    path('produtos/', admin_views.product_list, name='product_list'),
    path('produtos/novo/', admin_views.product_create, name='product_create'),
    path('produtos/<int:pk>/editar/', admin_views.product_edit, name='product_edit'),
    path('produtos/<int:pk>/toggle/', admin_views.product_toggle_active, name='product_toggle_active'),
    path('produtos/<int:pk>/excluir/', admin_views.product_delete, name='product_delete'),

    # Orders
    path('pedidos/', admin_views.order_list, name='order_list'),
    path('pedidos/<int:pk>/', admin_views.order_detail, name='order_detail'),
    path('pedidos/<int:pk>/status/', admin_views.order_update_status, name='order_update_status'),

    # Coupons
    path('cupons/', admin_views.coupon_list, name='coupon_list'),
    path('cupons/novo/', admin_views.coupon_create, name='coupon_create'),
    path('cupons/<int:pk>/editar/', admin_views.coupon_edit, name='coupon_edit'),
    path('cupons/<int:pk>/alternar/', admin_views.coupon_toggle_active, name='coupon_toggle_active'),
    path('cupons/<int:pk>/excluir/', admin_views.coupon_delete, name='coupon_delete'),

    # Categories
    path('categorias/', admin_views.category_list, name='category_list'),
    path('categorias/novo/', admin_views.category_create, name='category_create'),
    path('categorias/<int:pk>/editar/', admin_views.category_edit, name='category_edit'),
    path('categorias/<int:pk>/excluir/', admin_views.category_delete, name='category_delete'),
]
