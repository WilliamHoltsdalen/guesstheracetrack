from django.urls import path

from config.websocket import EchoConsumer
from config.websocket import websocket_application
from guesstheracetrack.games.consumers import TrackSegmentConsumer

websocket_urlpatterns = [
    path("", websocket_application),
    path("ws/echo/", EchoConsumer.as_asgi()),
    path("ws/track_segments/", TrackSegmentConsumer.as_asgi()),
]
