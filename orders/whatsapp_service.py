import urllib.parse
from django.conf import settings

def generate_whatsapp_link(order_draft):
    phone = getattr(settings, 'WHATSAPP_PHONE', '5511999999999')
    phone = "".join(filter(str.isdigit, str(phone)))
    
    text = f"Olá! Fiz o pedido #{order_draft.id} no site."

    if order_draft.customer_name:
        text += f" Sou {order_draft.customer_name}."

    if order_draft.phone:
        text += f" Meu WhatsApp/telefone: {order_draft.phone}."

    if order_draft.address:
        text += f" Endereço: {order_draft.address}"
        if order_draft.city:
            text += f", {order_draft.city}"
        text += "."

    text += " Pode confirmar, por favor?"

    encoded_text = urllib.parse.quote(text)

    return f"https://wa.me/{phone}?text={encoded_text}"
