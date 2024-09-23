from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework import status
from django.conf import settings
from django.http.response import JsonResponse
from api.models import User,Order, VariantCaterings
from api.serializers import OrderViewSerializer
from api.services import order_services
from drf_yasg.utils import swagger_auto_schema
from api.services.catering_services import get_specific_catering_object_by_id
from api.services.order_services import create_order_services, verify_signature
from django.conf import settings
from django.core.cache import cache
import requests
import json
import hashlib
from django.views.decorators.csrf import csrf_exempt
import json
from api.swagger_schemas import create_order_schema, get_order_schema


@swagger_auto_schema(**get_order_schema)
@swagger_auto_schema(**create_order_schema)
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
        catering = get_specific_catering_object_by_id(data["catering_id"])

        if catering != None:
            new_orders = create_order_services(data["variants"], catering)

            if new_orders != None:
                # Calculating total amount
                user = User.objects.get(id = user_id)
                total_amount = 0
                for new_order in new_orders:
                    total_amount += catering.price * new_order['quantity']
                    if new_order["variant"] != None:
                        variant = VariantCaterings.objects.get(id = new_order["variant"])
                        total_amount += variant.additional_price
                
                signature = settings.PAYMENT_GATEWAY_MERCHANT_CODE + data["catering_id"] + user.username + str(total_amount)  + settings.PAYMENT_GATEWAY_API_KEY
                
                # Create Request Structure
                request_body = {
                    "merchantCode": settings.PAYMENT_GATEWAY_MERCHANT_CODE,
                    "paymentAmount": total_amount,
                    "paymentMethod": settings.PAYMENT_GATEWAY_METHOD_CODE,
                    "merchantOrderId": data["catering_id"] + user.username,
                    "productDetails": "Pembayaran untuk catering makanan.",
                    "email": user.username+ "@gmail.com",
                    "customerVaName" : user.username,
                    "additionalParam": f"cart_{user_id}",
                    "returnUrl" : "https://example.com",
                    "callbackUrl" : settings.PAYMENT_GATEWAY_CALLBACK_URL,
                    "signature":hashlib.md5((signature).encode("utf-8")).hexdigest()
                }
                headers = {"Content-Type": "application/json"}
                request_body_json = json.dumps(request_body)
                endpoint_gateway = settings.PAYMENT_GATEWAY_URL + "/v2/inquiry"
                # print(f"!!! Signature: {signature}, Hashed signature: {hashlib.md5((signature).encode('utf-8')).hexdigest()}")
    
                # Send Request to Payment Gateway
                response = requests.post(endpoint_gateway, data=request_body_json, headers=headers, timeout=30)
                if response.status_code == 200:
                    response = response.json()
                    duitku_reference = response["reference"]
                    
                    data = {
                        "user_id" : user_id,
                        "variants" : data["variants"],
                        "notes" : data["notes"],
                        "catering_id" : data["catering_id"],
                        "amount" : total_amount,
                        "qrString" : response["qrString"]
                    }
                    cache.set(f"cart_{user_id}", json.dumps(data), timeout=100000)

                    # print(f"Reference: {duitku_reference}, Signature: {hashlib.md5((signature).encode("utf-8")).hexdigest()}, Cart name: cart_{user_id}")
                    return JsonResponse({
                        "order_list" : new_orders,
                        "qr_string" : response["qrString"], 
                        "amount" : response["amount"],
                        "ordered_by" : user_id,
                        }, status=status.HTTP_201_CREATED)
                else:
                    return JsonResponse({"message" : f"Oops something went wrong! {response.status_code}: {response.text}, {response.json()}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
            else:
                return JsonResponse({"message" : "New orders is not found"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return JsonResponse({"message" : "Catering not found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return JsonResponse({"message" : "Oops something went wrong" + str(e), "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@csrf_exempt 
def payment_callback(request):
    if request.method == 'POST':
        if request.content_type == 'application/x-www-form-urlencoded':
            data = request.POST.dict()
        else:
            return JsonResponse({'error': 'Invalid content type'}, status=400)
        
        required_fields = ['resultCode', 'amount', 'additionalParam', 'reference', 'signature', 'publisherOrderId']

        if not all(field in data for field in required_fields):
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        transaction_status = data['resultCode']
        publisher_order_id = data['publisherOrderId']
        
        if not verify_signature(data['signature'], data['merchantOrderId'], data['amount']):
            return JsonResponse({'error': 'Invalid signature'}, status=400)

        if transaction_status == '00':
            # Handle success logic (e.g., marking order as paid)
            jsonData = cache.get(data['additionalParam'])
            if jsonData == None:
                return JsonResponse({'error': 'Transaction data not found'}, status=404)

            try:
                order_data = json.loads(jsonData)
            except Exception:
                return JsonResponse({'error': 'Invalid JSON'}, status=400)
            
            catering = get_specific_catering_object_by_id(order_data["catering_id"])
            
            for variant in order_data["variants"]:
                order_services.save_order_to_database(order_data["user_id"], variant["quantity"], order_data["notes"], order_data["catering_id"], variant['variant_id'], publisher_order_id)
            
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'user_{order_data["user_id"]}',
                {
                    'type': 'payment_success',
                    'message': 'Payment success',
                    'publisherId': publisher_order_id,
                    'deliverDate': catering.date.strftime("%Y-%M-%d"),
                }
            )
            pass

        elif transaction_status == '01':
            # Handle failure logic
            pass

        return JsonResponse({'message': 'Callback received'}, status=200)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    

@csrf_exempt 
def payment_callback_pc(request):
    print("!!! Payment Callback Placeholder")
    if request.method == 'POST':
        if request.content_type == 'application/x-www-form-urlencoded':
            data = request.POST.dict()
        else:
            return JsonResponse({'error': 'Invalid content type'}, status=400)
        
        required_fields = ['resultCode', 'amount', 'additionalParam', 'reference', 'signature', 'publisherOrderId']

        if not all(field in data for field in required_fields):
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        transaction_status = data['resultCode']
        publisher_order_id = data['publisherOrderId']
        
        if not verify_signature(data['signature'], data['merchantOrderId'], data['amount']):
            return JsonResponse({'error': 'Invalid signature'}, status=400)

        if transaction_status == '00':
            # Handle success logic (e.g., marking order as paid)
            jsonData = cache.get(data['additionalParam'])
            if jsonData == None:
                return JsonResponse({'error': 'Transaction data not found'}, status=404)

            try:
                order_data = json.loads(jsonData)
            except Exception:
                return JsonResponse({'error': 'Invalid JSON'}, status=400)
            
            catering = get_specific_catering_object_by_id(order_data["catering_id"])
            
            for variant in order_data["variants"]:
                order_services.save_order_to_database(order_data["user_id"], variant["quantity"], order_data["notes"], order_data["catering_id"], variant['variant_id'], publisher_order_id)
            
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'user_{order_data["user_id"]}',
                {
                    'type': 'payment_success',
                    'message': 'Payment success',
                    'publisherId': publisher_order_id,
                    'deliverDate': catering.date.strftime("%Y-%M-%d"),
                }
            )
            pass

        elif transaction_status == '01':
            # Handle failure logic
            pass

        return JsonResponse({'message': 'Callback received'}, status=200)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)