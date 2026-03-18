import urllib.parse
from django.conf import settings

def generate_whatsapp_link(order_draft):
    phone = getattr(settings, 'WHATSAPP_PHONE', '5511999999999')
    phone = "".join(filter(str.isdigit, str(phone)))
    
    # Mensagem curta para evitar manipulação de valores
    text = f"Olá! Fiz o pedido #{order_draft.id} no site."

    if order_draft.customer_name:
        text += f" Sou {order_draft.customer_name}."

    text += " Pode confirmar, por favor?"

    if order_draft.city:
        text += f" Cidade: {order_draft.city}."

    encoded_text = urllib.parse.quote(text)

    return f"https://wa.me/{phone}?text={encoded_text}"
