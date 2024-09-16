from api.serializers import OrderSerializer
from api.models import Catering
from django.db import transaction
import datetime

# Probable error: Stock will be updated when the user bought something,
# So the create order doesn't check the stock before the user bought something properly

@transaction.atomic
def create_order_services(orders, catering : Catering):
    
    try:
        # Check if the stock is < then all the quantity order
        total_order = 0
        for order in orders:
            total_order += order["quantity"]
        
        if catering.stock >= total_order:
            catering.stock -= total_order
            catering.save()
            new_orders = []
            for order in orders:
                qty = order["quantity"]
                for _ in range(0, qty):
                    order['is_paid'] = False
                    order["quantity"]  = 1
                    if order["variant_id"] == "Reguler":
                        order["variant"] = None
                    else:
                        order["variant"] = order['variant_id']

                    new_orders.append(order)

            return new_orders
        
    except Exception as e :
        print(f"Erorr: {e}")
        return None
    
def save_order_to_database(ordered_by, quantity, notes, catering_id, variant_id): 
    new_order = {}
    try:
        new_order['is_paid'] = True
        new_order['ordered_by'] = ordered_by
        new_order['ordered_at'] = datetime.now()
        new_order['notes'] = notes
        new_order['quantity'] = quantity
        new_order['catering_id'] = catering_id
        if variant_id == "Reguler":
            new_order['variant'] = None
        else:
            new_order['variant'] = variant_id
        
        new_order = OrderSerializer(data=new_order)
        
        if new_order.is_valid(raise_exception=True):
            new_order.save()
            return new_order
    except Exception as e:
        print(f"Error: {e}")
        return None
    
    
# def verify_signature(merchant_code, data, signature):
#     signature = settings.PAYMENT_GATEWAY_MERCHANT_CODE + data["catering_id"] + user.username + str(total_amount) + settings.PAYMENT_GATEWAY_API_KEY