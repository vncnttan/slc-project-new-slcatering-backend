from api.serializers import OrderSerializer
from api.models import Order, Catering
from datetime import datetime
from django.http.response import JsonResponse
from rest_framework import status
from api.models import User, Order
from django.db import transaction
from django.conf import settings

@transaction.atomic
def create_order_services(user_id, orders, notes,catering : Catering):
    # TODO: Update logic for creating order through websocket with payment gateway
    try:
        #check if the stock is < then all the quantity order
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
                    order['ordered_by'] = user_id
                    order['ordered_at'] = datetime.now()
                    order["notes"] = notes
                    order["quantity"]  = 1
                    order['catering'] = catering.id
                    if order["variant_id"] == "Reguler":
                        order["variant"] = None
                    else:
                        order["variant"] = order['variant_id']
                    new_order = OrderSerializer(data=order)
                    if new_order.is_valid(raise_exception=True):
                        new_order.save()
                        new_orders.append(new_order)
            return new_orders
    except Exception as e :
        return None