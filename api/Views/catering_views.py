from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from django.http.response import JsonResponse
from rest_framework import status
from datetime import datetime
from api.serializers import CateringSerializer, CateringViewSerializer
from api.services import user_services, catering_services
from api.models import Catering
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# TODO: Tidy the method, migrate the logic to services
# TODO: Correct Documentation

@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            name="active",
            in_=openapi.IN_QUERY,
            type=openapi.TYPE_BOOLEAN,
            description="Get active caterings",
            required=True
        )
    ],
    responses={
        200 : "Succesfull response",
        401 : "Access denied",
        500 : "Unexpected error"       
    }
)
@swagger_auto_schema(
    method="post",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "title" : openapi.Schema(type=openapi.TYPE_STRING, description="Catering title"),
            "price" : openapi.Schema(type=openapi.TYPE_INTEGER, description="Price"),
            "stock" : openapi.Schema(type=openapi.TYPE_INTEGER, description="Catering maximum order"),
            "catering_variants" : openapi.Schema(
                type=openapi.TYPE_ARRAY,
                description="Catering variants",
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "variant_name" : openapi.Schema(type=openapi.TYPE_STRING, description="Catering variant name"),
                        "additional_price": openapi.Schema(type=openapi.TYPE_INTEGER, description="Catering variant extra price")
                    }
                ),
                required=["variant_name", "additional_price"]
            ),
        },
        required=["name", "price", "stock", "date", "catering_variants"]
    ),
    responses={
        201 : "Succesfully created catering",
        400 : "Bad request",
        401 : "Not authorized",
        406 : "Failed to process data",
        500 : "Unexpected error"
    }
)
@swagger_auto_schema(
    method="patch",
    operation_description=(
        "Close catering. "
        "This endpoint will ask for catering id and will close it. "
        "It will also validate that the catering can be closed only by its creator."
    ),
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "catering_id" : openapi.Schema(type=openapi.TYPE_STRING, description="Catering id to be closed")
        },
        required=['catering_id']
    ),
    responses={
        200 : "Sucesfully closed catering",
        404 : "Catering not found",
        500 : "Unexpected error"
    }
)
@api_view(["GET", "POST", "PATCH"])
def catering(request):
    if request.method == "GET":
        if request.GET.get('active') == "true":
            return get_active_caterings(request)
        elif request.GET.get('active') == "false":
            try:
                curr_user = user_services.get_spesific_user_by_id(request.user_id)
                if(curr_user.role == "merchant"):
                    catering = catering_services.get_all_caterings_by_merchant(request.user_id)
                    if catering == None:
                        return JsonResponse([], status=status.HTTP_200_OK)
                    return JsonResponse(catering.data, status=status.HTTP_200_OK, safe=False)
                else:
                    return JsonResponse({"message" : "Access denied"}, status=status.HTTP_401_UNAUTHORIZED)
            except AttributeError as e:
                return JsonResponse({"message" : "Access denied disini"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e :
                return JsonResponse({"message" : "Oops something went wrong", "error" : str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Most Popular Menu

        if request.GET.get('id'):
            catering = catering_services.get_specific_catering_by_id(request.GET.get('id'))
            if catering == None:
                return JsonResponse({"message" : "Catering does not exist"}, status=status.HTTP_404_NOT_FOUND)
            else:
                return JsonResponse(catering.data, status=status.HTTP_200_OK, safe=False)
        
        catering = catering_services.get_all_caterings()
        if catering == None:
            return JsonResponse({"message" : "Catering does not exist"}, status=status.HTTP_404_NOT_FOUND)
        else:
            return JsonResponse(catering.data, status=status.HTTP_200_OK, safe=False)
    elif request.method == "POST":
        return create_catering(request)
    elif request.method == "PATCH":
        return close_catering(request)

def close_catering(request):
    data = JSONParser().parse(request)
    try:
        catering = Catering.objects.get(id=data['catering_id'])
        user = user_services.get_spesific_user_by_id(request.user_id)
        if 'catering_id' in data and catering is not None and catering.is_closed is False and catering.created_by == user.id:
            catering.is_closed = True
            catering.save()
            return JsonResponse({"message": "Succesfully closed catering"}, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"message": "Catering not found"}, status=status.HTTP_404_NOT_FOUND)
    except(Catering.DoesNotExist):
        return JsonResponse({"message":"Catering not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e :
        return JsonResponse({"message" : "Bad Request", "error" : str(e) }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def get_active_caterings(request):
    caterings = catering_services.get_active_caterings()
    if caterings is not None :
        return JsonResponse(caterings.data,safe=False, status=status.HTTP_200_OK)
    else:
        return JsonResponse([], status=status.HTTP_200_OK)


def create_catering(request):
    try :
        data = JSONParser().parse(request)
        if data['title'] == "" or data["price"] == 0:
            return JsonResponse({"message":"Fill in all the fields"}, status=status.HTTP_400_BAD_REQUEST)
        
        user = user_services.get_spesific_user_by_id(request.user_id)
        
        if not user or user.role != 'merchant':
            return JsonResponse({"message" : "Your account is not authorized to create a catering"}, status=status.HTTP_401_UNAUTHORIZED)
        
        data["created_at"] = datetime.now()
        data['created_by'] = user.id
        data['is_closed'] = False
        
        serializer = CateringSerializer(data=data)
        if serializer.is_valid():
            try:
                serializer.save()
                return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                print(f"Error: {str(e)}")
                return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else :
            print(serializer.errors)
            return JsonResponse({'message' : 'Failed to proccess data'}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except Exception as e:
        return JsonResponse({"message" : "Ooops something went wrong", "error" : str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)