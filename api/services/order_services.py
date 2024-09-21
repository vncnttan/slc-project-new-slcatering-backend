from api.serializers import OrderSerializer
from api.models import Catering
from django.db import transaction
from datetime import datetime
import hashlib
from django.conf import settings

# Probable error: Stock will be updated when the user bought something,
# So the create order doesn't check the stock before the user bought something properly

@transaction.atomic
def create_order_services(orders, catering: Catering):
    
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
                order['is_paid'] = False
                if order["variant_id"] == "Reguler":
                    order["variant"] = None
                else:
                    order["variant"] = order['variant_id']

                new_orders.append(order)

            return new_orders
        else:
            return None
        
    except Exception as e :
        print(f"Erorr: {e}")
        return None
    
def save_order_to_database(ordered_by, quantity, notes, catering_id, variant_id, publisher_order_id): 
    new_order = {}
    try:
        new_order['is_paid'] = True
        new_order['ordered_by'] = ordered_by
        new_order['ordered_at'] = datetime.now()
        new_order['notes'] = notes
        new_order['quantity'] = quantity
        new_order['publisher_order_id'] = publisher_order_id
        new_order['catering'] = catering_id
        if variant_id == "Reguler":
            new_order['variant'] = None
        else:
            new_order['variant'] = variant_id
        
        new_order = OrderSerializer(data=new_order)
        
        if new_order.is_valid(raise_exception=True):
            print(f"Saving order to database {new_order}")
            new_order.save()
            
            return new_order
        else:
            print(f"Error: {new_order.errors}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None
    
    
def verify_signature(hashed_signature, merchant_order_id, total_amount):
    signature = settings.PAYMENT_GATEWAY_MERCHANT_CODE + merchant_order_id + total_amount + settings.PAYMENT_GATEWAY_API_KEY
    calculated_signature = hashlib.md5(signature.encode("utf-8")).hexdigest()
    print(f"\t Verifying signature hash of {signature}, {calculated_signature} == {hashed_signature}")
    return hashed_signature == calculated_signature
