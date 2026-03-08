from django.test import TestCase
from .models import OrderDraft
from .whatsapp_service import generate_whatsapp_link
from decimal import Decimal

class WhatsAppServiceTests(TestCase):
    def test_generate_whatsapp_link(self):
        draft = OrderDraft.objects.create(
            customer_name='João Silva',
            city='São Paulo',
            delivery_option='Retirar no local',
            notes='Entregar à tarde',
            total_estimated=Decimal('150.00'),
            items_json=[
                {
                    'product_name': 'Vaso Geométrico',
                    'quantity': 2,
                    'color': 'Preto',
                    'unit_price': '50.00',
                    'custom_fields': {'Tamanho': 'Médio'}
                },
                {
                    'product_name': 'Peça Customizada',
                    'quantity': 1,
                    'color': '',
                    'unit_price': '50.00',
                    'custom_fields': {'Texto': 'Feliz Aniversário'}
                }
            ]
        )
        
        link = generate_whatsapp_link(draft)
        
        self.assertTrue('https://wa.me/' in link)
        self.assertTrue('text=' in link)
        
        # O link tem que conter os dados encondados (João Silva, Vaso Geométrico, etc)
        self.assertTrue('Jo%C3%A3o%20Silva' in link)
        self.assertTrue('Vaso%20Geom%C3%A9trico' in link)
        self.assertTrue('Total%20Estimado%3A%20R%24%20150.00' in link)
