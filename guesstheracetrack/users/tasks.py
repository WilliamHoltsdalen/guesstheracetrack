import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .models import User

logger = logging.getLogger(__name__)


@shared_task()
def get_users_count():
    """A pointless Celery task to demonstrate usage."""
    return User.objects.count()


@shared_task()
def cleanup_fake_users():
    """
    Clean up fake users who haven't logged in within 15 minutes of registration.
    These are likely bot accounts that never verified their email or logged in.
    """
    # Calculate the cutoff time (15 minutes ago)
    cutoff_time = timezone.now() - timedelta(minutes=15)

    fake_users = User.objects.filter(
        last_login__isnull=True,
        date_joined__lt=cutoff_time,
    )

    count = fake_users.count()

    if count > 0:
        logger.info(
            "Cleaning up %d fake users (registered before %s)",
            count,
            cutoff_time,
        )

        fake_users.delete()

        logger.info("Successfully deleted %d fake users", count)
        return f"Deleted {count} fake users"
    logger.info("No fake users found to clean up")
    return "No fake users found to clean up"
