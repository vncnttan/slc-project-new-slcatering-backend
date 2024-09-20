from django.urls import re_path
from .consumers import QRCodeConsumer

websocket_urlpatterns = [
    re_path(r"ws/qrcode/(?P<user_id>[\w-]+)/$", QRCodeConsumer.as_asgi()),
]