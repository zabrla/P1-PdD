from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(
        r"^ws/signaling/(?P<room_name>[\w-]{3,64})/$",
        consumers.SignalingConsumer.as_asgi(),
    ),
]
