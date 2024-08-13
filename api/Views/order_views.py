from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from rest_framework import status
import jwt
from django.conf import settings
from django.http.response import JsonResponse
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from api.models import User,Order, Catering, VariantCaterings
from api.serializers import OrderViewSerializer
from api.services import order_services, user_services
from django.contrib.auth.hashers import make_password, check_password
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from api.services.catering_services import get_specific_catering_by_id
from api.services.variant_services import get_variant_by_id
from api.services.order_services import create_order_services
from django.conf import settings
import requests
import json
import hashlib

@swagger_auto_schema(
    method='get',
    operation_description=(
        "Retrive orders. "
        "If there is id in the request parameter, then it will get all order from a catering. "
        "If there is no id in the request parameter, then it will get all order from a current logged in user."
    ),
    manual_parameters=[
        openapi.Parameter(
            name='id',
            in_= openapi.IN_QUERY,
            type=openapi.TYPE_STRING,
            description="Get all order from a spesific catering",
            required=False
        ),
    ],
    responses={
        200: "Succesfull response",
        403 : "Access denied",
        500 : "Unexpected error"
    }
)
@swagger_auto_schema(
    method='post',
    operation_description=(
        "Create orders. "
        "Create catering orders for users and generate the qr code for payment"
    ),
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "catering_id" : openapi.Schema(type=openapi.TYPE_STRING, description="Catering id used to determine which catering user wants to order"),
            "variants": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "variant_id": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="variant_id used to determine the variant wanted to be bought buy the user"
                            ),
                        "quantity": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="Quantity used to determine the total of the variant to be bought"
                        ),
                    }
                    
                ),
                description="Variants is a list of the variants ordered by the user"
            ),
            "notes" : openapi.Schema(
                type=openapi.TYPE_STRING, 
                description="User notes for the seller"
                )
        },
        required=['catering', 'variants', 'notes']
        
    ),
    responses={
        200 : "Succesfull response",
        400 : "Bad request",
        403 : "Authentication needed",
        406 : "Out of stock",
        500 : "Unexpected error"
    }
)
@api_view(["POST", "GET"])
def order(request):
    if request.method == "POST":
        return create_order(request)
    elif request.method == "GET":
        return get_orders(request)

def get_orders(request):
    try:
        id = request.GET.get('id')
        if id:
            order = Order.objects.filter(catering = id)
            order_serializer = OrderViewSerializer(order, many=True).data
            return JsonResponse(order_serializer, status=status.HTTP_200_OK, safe=False)
        elif request.user_id:
            order = Order.objects.filter(ordered_by = request.user_id)
            serializer_order = OrderViewSerializer(order, many=True).data
            return JsonResponse(serializer_order, status=status.HTTP_200_OK, safe=False)
    except AttributeError:
        return JsonResponse({"message":"Access denied!"}, status=status.HTTP_403_FORBIDDEN)
    except Exception as e :
        return JsonResponse({"message": "Oops something went wrong", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def create_order(request):
    try:
        user_id = request.user_id
        data = JSONParser().parse(request)
        catering = get_specific_catering_by_id(data["catering_id"])
        if catering != None:
            new_orders = create_order_services(user_id, data["variants"], data["notes"],catering)
            if new_orders != None:
                order_ids = [order.data['id'] for order in new_orders]
                # concatenated_order_ids = '#'.join(map(str, order_ids))
                
                user = User.objects.get(id = user_id)
                total_amount = 0
                for new_order in new_orders:
                    catering = Catering.objects.get(id = new_order.data["catering"])
                    total_amount += catering.price
                    if new_order.data["variant"] != None:
                        variant = VariantCaterings.objects.get(id = new_order.data["variant"])
                        total_amount += variant.additional_price
                        
                        
                request_body = {
                    "merchantCode": settings.PAYMENT_GATEWAY_MERCHANT_CODE,
                    "paymentAmount": total_amount,
                    "paymentMethod": settings.PAYMENT_GATEWAY_METHOD_CODE,
                    "merchantOrderId": order_ids[0],
                    "productDetails": "Pembayaran untuk catering makanan.",
                    "email": user.username+ "@gmail.com",
                    "customerVaName" : user.username,
                    "returnUrl" : "https://example.com",
                    "callbackUrl" : settings.PAYMENT_GATEWAY_CALLBACK_URL,
                    "signature":hashlib.md5((settings.PAYMENT_GATEWAY_MERCHANT_CODE + order_ids[0] + str(total_amount) + settings.PAYMENT_GATEWAY_API_KEY).encode("utf-8")).hexdigest()
                }
                headers = {"Content-Type": "application/json"}
                request_body_json = json.dumps(request_body)
                endpoint_gateway = settings.PAYMENT_GATEWAY_URL + "/v2/inquiry"
    
                response = requests.post(endpoint_gateway, data=request_body_json, headers=headers, timeout=30)
                if response.status_code == 200:
                    response = response.json()
                    duitku_reference = response["reference"]
                    
                    list_order_view_serializer = []
                    for new_order in new_orders:
                        order_obj = Order.objects.get(id = new_order.data["id"])
                        order_obj.duitku_reference = duitku_reference
                        order_obj.save()
                        order_view_serializer = OrderViewSerializer(instance=order_obj).data
                        list_order_view_serializer.append(order_view_serializer)
                    
                    
                    return JsonResponse({
                        "order_list" : list_order_view_serializer,
                        "qrString" : response["qrString"], "amount" : response["amount"],
                        }, status=status.HTTP_201_CREATED)
                else:
                    return JsonResponse({"message" : "Oops something went wrong" + response.text + str(response.status_code)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
            else:
                return JsonResponse({"message" : "Oops something went wrong" + str(e), "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    except Exception as e:
        print(e)
        return JsonResponse({"message" : "Oops something went wrong" + str(e), "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)