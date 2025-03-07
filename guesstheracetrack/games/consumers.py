import json

from channels.generic.websocket import AsyncWebsocketConsumer


class TrackSegmentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "track_segments"

        # Join room group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )

        await self.accept()

        # Test sending a message immediately upon connection
        await self.send(
            text_data=json.dumps(
                {
                    "message": "Connection established",
                },
            ),
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name,
        )

    async def receive(self, text_data):
        # Echo back received messages
        await self.send(text_data=text_data)

    async def send_segments(self, event):
        await self.send(text_data=json.dumps(event))
