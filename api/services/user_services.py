from rest_framework.parsers import JSONParser
from rest_framework import status
from api.models import User
from api.serializers import UserSerializer
from django.http.response import JsonResponse
from django.db.models import Count

def get_spesific_user_by_id(id):
    try:
        user = User.objects.get(id=id)
        return user
    except User.DoesNotExist:
        return None

def get_spesific_user_by_username(username):
    try:
        user = User.objects.get(username=username)
        return user
    except User.DoesNotExist:
        return None
    
def get_top_customer():
    try:
        users = User.objects.annotate(
            total_order=Count('ordered_by')
        ).order_by('-total_order')[:5]
        users_serializer = UserSerializer(users, many=True)
        return users_serializer
    except User.DoesNotExist:
        return None