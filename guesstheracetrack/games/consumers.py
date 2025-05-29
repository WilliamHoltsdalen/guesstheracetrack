import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer


class TrackSegmentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get the user's active game session to create a unique group name
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return

        # Import here to avoid Django app loading issues
        from .services import get_active_game_session

        game_session = await sync_to_async(get_active_game_session)(
            user,
            "competitive_mode",
        )
        if not game_session:
            await self.close()
            return

        # Store game session for later use
        self.game_session = game_session
        self.group_name = f"track_segments_{game_session.id}"

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
                    "group": self.group_name,
                },
            ),
        )

    async def disconnect(self, close_code):
        from .tasks import cancel_send_segments_task

        # Cancel task for this specific session
        if hasattr(self, "game_session"):
            await sync_to_async(cancel_send_segments_task, thread_sensitive=False)(
                self.game_session.id,
            )

        # Leave room group
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )

    async def receive(self, text_data):
        # Echo back received messages
        await self.send(text_data=text_data)

    async def send_segments(self, event):
        await self.send(text_data=json.dumps(event))
