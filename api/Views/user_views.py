from django.http.response import JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework import status
from api.services import user_services, catering_services
from api.models import User
from api.serializers import UserSerializer
from rest_framework.decorators import api_view
from rest_framework_simplejwt.tokens import AccessToken
import requests
from api.services.user_services import get_spesific_user_by_username
from drf_yasg.utils import swagger_auto_schema
from api.swagger_schemas import get_user_schema, delete_user_schema, get_leaderboard_schema, login_schema

@swagger_auto_schema(**get_user_schema)
@swagger_auto_schema(**delete_user_schema)
@api_view(["GET", "DELETE"])
def user(request):
    if request.method == "GET":
        return get_user(request)
    elif request.method == "DELETE":
        return delete_user(request)


@swagger_auto_schema(**get_leaderboard_schema)
@api_view(["GET"])
def leaderboards(request):
    if request.method == "GET":
        if request.GET.get('menu') == "true":
            caterings = catering_services.get_popular_caterings()
            if caterings is not None :
                return JsonResponse(caterings.data, safe=False, status=status.HTTP_200_OK)
            else:
                return JsonResponse([], status=status.HTTP_200_OK)
        else:
            users = user_services.get_top_customer()
            if users is not None:
                return JsonResponse(users.data, safe=False, status=status.HTTP_200_OK)
            else:
                return JsonResponse([], status=status.HTTP_200_OK)

@swagger_auto_schema(**login_schema)
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
        # Use this if need extra data such as Full Name, etc.
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


def get_all_user():
    try:
        users_data = user_services.get_all_user()
        return JsonResponse(users_data, status=status.HTTP_200_OK, safe=False)
    except Exception as e:
        return JsonResponse(
            {"message": "An error occurred while fetching users", "error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def get_user(request):
    try:
        user_id = request.user_id
        user = user_services.get_spesific_user_by_id(user_id)
        user_data = UserSerializer(user).data
        return JsonResponse(user_data, status=status.HTTP_200_OK)
    except Exception as e:
        return JsonResponse({"message" : "Oops something went wrong !", "error" : str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def delete_user(request):
    try:
        current_user_id = request.user_id.replace('-', '')
        data = JSONParser().parse(request)
        deleted_username = user_services.delete_user_by_id(data['user_id'], current_user_id)
        return JsonResponse({"message": f"Successfully deleted {deleted_username}"}, status=status.HTTP_200_OK)
    except(User.DoesNotExist):
        return JsonResponse({"message": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return JsonResponse({"message": "Oops something went wrong", "error" : str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
