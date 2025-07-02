from channels.consumer import AsyncConsumer


async def websocket_application(scope, receive, send):
    while True:
        event = await receive()

        if event["type"] == "websocket.connect":
            await send({"type": "websocket.accept"})

        if event["type"] == "websocket.disconnect":
            break

        if event["type"] == "websocket.receive":
            if event["text"] == "ping":
                await send({"type": "websocket.send", "text": "pong!"})


class EchoConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        await self.send(
            {
                "type": "websocket.accept",
            },
        )

    async def websocket_receive(self, event):
        await self.send(
            {
                "type": "websocket.send",
                "text": event["text"],
            },
        )
