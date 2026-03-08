from django.urls import path
from . import admin_views

app_name = 'custom_admin'

urlpatterns = [
    path('', admin_views.dashboard, name='dashboard'),
    path('cupons/novo/', admin_views.coupon_create, name='coupon_create'),
    path('cupons/<int:pk>/alternar/', admin_views.coupon_toggle_active, name='coupon_toggle_active'),
    path('produtos/novo/', admin_views.product_create, name='product_create'),
]
