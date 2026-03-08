from django.contrib import admin
from .models import UserCart


@admin.register(UserCart)
class UserCartAdmin(admin.ModelAdmin):
	list_display = ('user', 'updated_at')
	search_fields = ('user__username', 'user__email')
