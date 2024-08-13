from typing import Any
from django.http.response import HttpResponse, JsonResponse
from api.models import User
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework import status
import jwt
from django.conf import settings
from api.models import User

class AuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.protected_endpoints = [
            '/api/user',
            '/api/catering',
        ]
    
    def __call__(self, request) -> Any:
        if (any(request.path.startswith(endpoint) for endpoint in self.protected_endpoints) and (request.method == "POST" or request.method == "PUT" or request.method == "PATCH")):
            auth_header = request.META.get('HTTP_AUTHORIZATION')
            if auth_header:
                try:
                    get_auth_by_header(auth_header, request)
                except (InvalidToken, TokenError, User.DoesNotExist):
                    return JsonResponse({"message" : "Invalid token !"}, status=status.HTTP_401_UNAUTHORIZED)
                except jwt.ExpiredSignatureError:
                    return JsonResponse({"message" : "Token expired !"}, status=status.HTTP_406_NOT_ACCEPTABLE)
            else:
                return JsonResponse({'message':'Access Denied!'}, status=status.HTTP_401_UNAUTHORIZED)
        return self.get_response(request)

class SellerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.protected_endpoints = [
            '/api/catering',
        ]
    
    def __call__(self, request) -> Any:
        if (any(request.path.startswith(endpoint) for endpoint in self.protected_endpoints) and (request.method == "POST" or request.method == "PUT" or request.method == "PATCH" or request.method == "DELETE")):
            try:    
                user = User.objects.get(id = request.user_id)
                request.user = user
                if user.role != 'merchant':
                    return JsonResponse({"message":"Access Denied!"}, status=status.HTTP_401_UNAUTHORIZED)
            except(User.DoesNotExist):
                return JsonResponse({"message":"Access Denied!"}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            auth_header = request.META.get('HTTP_AUTHORIZATION')
            if auth_header and request.path == "/api/catering" and request.method == "GET":
                try:
                    get_auth_by_header(auth_header, request)
                except (InvalidToken, TokenError, User.DoesNotExist):
                    return JsonResponse({"message" : "Invalid token !"}, status=status.HTTP_401_UNAUTHORIZED)
                except jwt.ExpiredSignatureError:
                    return JsonResponse({"message" : "Token expired !"}, status=status.HTTP_406_NOT_ACCEPTABLE)
            pass
        
        return self.get_response(request)

class OrderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.protected_endpoints = [
            '/api/order'
    ]
    
    def __call__(self, request) -> Any:
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if auth_header:
            try:
                token_type, token = auth_header.split(' ')
                if token_type == 'Bearer':
                    token = token.encode('utf-8')
                    decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                    request.user_id = decoded_token.get('user_id')
            except Exception as e :
                self.get_response(request)
        return self.get_response(request)
            

# TODO: Migrate to helper
def get_auth_by_header(auth_header, request):
    try:
        token_type, token = auth_header.split(' ')
        if token_type == 'Bearer':
            token = token.encode('utf-8')
            print("Token: ", token)
            decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            print("Decoded Token: ", decoded_token)
            request.user_id = decoded_token.get('user_id')
            print("User ID: ", request.user_id)
        else:
            return JsonResponse({'message':'Access Denied!'}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return JsonResponse({"message": "Access Denied"}, status=status.HTTP_401_UNAUTHORIZED)