from django.contrib import admin
from .models import OrderDraft, Coupon

@admin.register(OrderDraft)
class OrderDraftAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer_name', 'total_estimated', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['customer_name', 'city', 'id']
    readonly_fields = ['created_at']


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_percent', 'category', 'active', 'valid_from', 'valid_to', 'usage_count', 'max_uses']
    list_filter = ['active', 'category']
    search_fields = ['code']
