import time

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer

from config.celery_app import app as celery_app

TIME_BETWEEN_SENDING_SEGMENTS = 1


@shared_task(name="games.tasks.send_segments_task")
def send_segments_task(segments, room_name):
    channel_layer = get_channel_layer()
    for segment in segments:
        async_to_sync(channel_layer.group_send)(
            room_name,
            {
                "type": "send_segments",
                "message": segment,
            },
        )
        time.sleep(TIME_BETWEEN_SENDING_SEGMENTS)


def cancel_send_segments_task():
    """Cancel the send segments task."""
    inspector = celery_app.control.inspect()
    active_tasks = inspector.active()
    if active_tasks:
        for tasks in active_tasks.values():
            for task in tasks:
                if task["name"] == "games.tasks.send_segments_task":
                    celery_app.control.revoke(task["id"], terminate=True)
