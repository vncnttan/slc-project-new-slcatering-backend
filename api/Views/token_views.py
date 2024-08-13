from rest_framework_simplejwt.views import TokenRefreshView
from django.http import JsonResponse
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework.response import Response
from rest_framework import status

class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        data = {'refresh': refresh_token}
        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e :
            raise InvalidToken(e.args[0])
        response = Response(serializer.validated_data, status=status.HTTP_200_OK)
        access_token = response.data.pop('access')
        response.set_cookie('access_token', access_token, httponly=True, samesite='Lax')
        response.data = {'message': 'Succesfully refreshed access token'}
        return response