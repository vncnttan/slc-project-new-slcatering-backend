from django.shortcuts import render
from django.http.response import JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework import status
from django.contrib.auth.hashers import make_password, check_password
from rest_framework import permissions
from api.services import user_services, catering_services
from api.models import User
from api.serializers import UserSerializer
from rest_framework.decorators import api_view, permission_classes
from datetime import datetime
from django.core.mail import send_mail
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken,AccessToken
from django.template.loader import render_to_string
import base64
import jwt
import requests
from api.services.user_services import get_spesific_user_by_username
from django.http import HttpResponse
from datetime import datetime, timedelta
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Create your views here.

@swagger_auto_schema(
    method='get',
    security=[{'Bearer': []}],
    operation_description=(
        "Retrieve specific user data based on the Authorization Token."
    ),
    manual_parameters=[
        openapi.Parameter(
            name='all',
            in_=openapi.IN_QUERY,
            type=openapi.TYPE_BOOLEAN,
            description="Get all users parameter",
            required=False
        ),
    ],
    responses={
        200:"Succesfull response",
        500: "Unexpected error"
    }
)
@swagger_auto_schema(
    method='delete',
    security=[{'Bearer': []}],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'user_id' : openapi.Schema(type=openapi.TYPE_STRING, description="User id to be deleted")
        },
        required=['user_id']
        
    ),
    responses={
        200:"Succesfully response",
        406 : "You cannot delete your own account",
        404: "User does not exist",
        500 : "Unexpected error"
    }
)
@api_view(["GET", "DELETE"])
def user(request):
    if request.method == "GET":
        return get_user(request)
    elif request.method == "DELETE":
        return delete_user(request)

@api_view(["GET"])
def leaderboards(request):
    if request.method == "GET":
        if request.GET.get('menu') == "true":
            caterings = catering_services.get_popular_caterings()
            if caterings is not None :
                return JsonResponse(caterings.data,safe=False, status=status.HTTP_200_OK)
            else:
                return JsonResponse([], status=status.HTTP_200_OK)
        else:
            users = user_services.get_top_customer()
            if users is not None:
                return JsonResponse(users.data, safe=False, status=status.HTTP_200_OK)
            else:
                return JsonResponse([], status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'username' : openapi.Schema(type=openapi.TYPE_STRING, description="Fill in with username"),
            'password' : openapi.Schema(type=openapi.TYPE_STRING, description="Fill in with password")
        },
        required=['username', 'password']
    ),
    responses={
        200: "Succesfull response",
        400: "Invalid username / password",
        500: "Unexpected error"
    }
)
@api_view(['POST'])
def login(request):
    try: 
        data = JSONParser().parse(request)
        if not "username" in data or not "password" in data:
            return JsonResponse({"message": "Username and password must be filled"}, status=status.HTTP_400_BAD_REQUEST)
        
        if data["username"] == "" or data["password"] == "":
            return JsonResponse({"message": "Username and password must be filled"}, status=status.HTTP_400_BAD_REQUEST)
        
        username = data['username']
        password = data['password']

        base_url = "https://bluejack.binus.ac.id/lapi/api/Account/"
        messier_login_token = requests.post(base_url + "LogOn", data={"username": username, "password": password}).json()

        print(username, password, messier_login_token)
        if not "access_token" in messier_login_token:
            return JsonResponse({"message": "Invalid username / password"}, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return JsonResponse({"message": "Oops something went wrong", "error" : str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)   
        
    # Try to get user data, if not exist, register from Messier
    user = get_spesific_user_by_username(username)

    if not user:
        # use this if need extra data such as Full Name, etc.
        # messier_login_token = messier_login_token["access_token"]
        # messier_user_data = requests.get(base_url + "Me", headers={"Authorization": "Bearer " + messier_login_token}).json() 

        # Register new user
        serializer = UserSerializer(data={
            "username": username,
            "role": "customer",
        })
        if serializer.is_valid():
            user = serializer.save()

    access_token = AccessToken().for_user(user=user)
    return JsonResponse({'access_token' : str(access_token), 'message': 'Login Succesfully !'}, status=status.HTTP_200_OK)

# Custom Functions for User -> Soon will be moved to services
def get_all_user():
    users = User.objects.all()
    users_serializer = UserSerializer(users, many=True).data
    return JsonResponse(users_serializer, status=status.HTTP_200_OK, safe=False)

def get_user(request):
    try:
        user_id = request.user_id
        user = User.objects.get(id=str(user_id))
        ser_data = UserSerializer(user).data
        # ser_data.pop('password')
        return JsonResponse(ser_data, status=status.HTTP_200_OK)
    except Exception as e:
        return JsonResponse({"message" : "Oops something went wrong !", "error" : str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def delete_user(request):
    try:
        curr_userid = request.user_id.replace('-', '')
        data = JSONParser().parse(request)
        if(curr_userid == data['user_id'].replace('-', '')):
            return JsonResponse({"message":"You cannot delete your own account"}, status=status.HTTP_406_NOT_ACCEPTABLE)
        user = User.objects.get(id=data["user_id"])
        user_delete_username = user.username
        user.delete()
        return JsonResponse({"message": "Successfully deleted "+user_delete_username}, status=status.HTTP_200_OK)
    except(User.DoesNotExist):
        return JsonResponse({"message": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return JsonResponse({"message": "Oops something went wrong", "error" : str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
