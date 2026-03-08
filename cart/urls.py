from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail, name='cart_detail'),
    path('adicionar/<int:product_id>/', views.cart_add, name='cart_add'),
    path('remover/<str:item_id>/', views.cart_remove, name='cart_remove'),
    path('atualizar/<str:item_id>/', views.cart_update, name='cart_update'),
    path('aplicar-cupom/', views.apply_coupon, name='apply_coupon'),
]
