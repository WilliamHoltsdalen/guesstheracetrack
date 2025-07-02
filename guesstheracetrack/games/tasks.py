import time

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer

from config.celery_app import app as celery_app

TIME_BETWEEN_SENDING_SEGMENTS = 1


@shared_task(name="games.tasks.send_segments_task")
def send_segments_task(segments, room_name):
    """Send segments to a room group, with a delay between each segment."""
    channel_layer = get_channel_layer()

    # Send immediate start message
    async_to_sync(channel_layer.group_send)(
        room_name,
        {
            "type": "send_segments",
            "message": {"type": "start", "total_segments": len(segments)},
        },
    )

    for i, segment in enumerate(segments):
        # Send first segment immediately, then add delay for subsequent ones
        if i > 0:
            time.sleep(TIME_BETWEEN_SENDING_SEGMENTS)

        async_to_sync(channel_layer.group_send)(
            room_name,
            {
                "type": "send_segments",
                "message": segment,
            },
        )


def cancel_send_segments_task(session_id):
    """Cancel the send segments task for the session with the given id."""
    inspector = celery_app.control.inspect()
    active_tasks = inspector.active()
    if active_tasks:
        for tasks in active_tasks.values():
            for task in tasks:
                if task["name"] == "games.tasks.send_segments_task":
                    # Extract session_id from the room_name argument
                    task_args = task.get("args", [])
                    if len(task_args) >= 2:  # noqa: PLR2004
                        room_name = task_args[1]
                        if room_name == f"track_segments_{session_id}":
                            celery_app.control.revoke(task["id"], terminate=True)
