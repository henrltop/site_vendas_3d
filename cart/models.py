from django.conf import settings
from django.db import models


class UserCart(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
	data = models.JSONField(default=dict, blank=True)
	coupon_id = models.IntegerField(null=True, blank=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		verbose_name = 'Carrinho do usuário'
		verbose_name_plural = 'Carrinhos dos usuários'

	def __str__(self):
		return f'Carrinho de {self.user}'
