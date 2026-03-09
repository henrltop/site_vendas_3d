import urllib.parse
from django.conf import settings

def generate_whatsapp_link(order_draft):
    phone = getattr(settings, 'WHATSAPP_PHONE', '5511999999999')
    phone = "".join(filter(str.isdigit, str(phone)))
    
    # Montando a mensagem
    text = f"Olá! Gostaria de fazer o pedido #{order_draft.id}\n"
    text += f"Nome: {order_draft.customer_name}\n\n"
    
    text += "🛒 ITENS:\n"
    
    # Tratando a lista de itens salva no json
    items = order_draft.items_json if isinstance(order_draft.items_json, list) else []
    
    for item in items:
        qty = item.get('quantity', 1)
        name = item.get('product_name', 'Produto Desconhecido')
        color = item.get('color')
        
        color_str = f" (Cor: {color})" if color else ""
        text += f"{qty}x {name}{color_str}\n"
        
        custom_fields = item.get('custom_fields', {})
        for k, v in custom_fields.items():
            text += f" - {k}: {v}\n"
            
        unit_price = float(item.get('unit_price', 0))
        text += f" - Valor Unitário: R$ {unit_price:.2f}\n\n"
        
    text += f"💰 Subtotal: R$ {float(order_draft.total_estimated):.2f}\n"
    if order_draft.discount_amount and order_draft.discount_amount > 0:
        text += f"💸 Desconto: -R$ {float(order_draft.discount_amount):.2f}\n"
    if order_draft.coupon:
        text += f"🏷️ Cupom: {order_draft.coupon.code}\n"
    total_final = order_draft.total_after_discount or order_draft.total_estimated
    text += f"💰 *Total: R$ {float(total_final):.2f}*\n\n"
    
    if order_draft.city:
        text += f"📍 Cidade: {order_draft.city}\n"
    if order_draft.delivery_option:
        text += f"🚚 Entrega: {order_draft.delivery_option}\n"
    if order_draft.notes:
        text += f"📝 Observações: {order_draft.notes}\n"
        
    encoded_text = urllib.parse.quote(text)
    
    return f"https://wa.me/{phone}?text={encoded_text}"
