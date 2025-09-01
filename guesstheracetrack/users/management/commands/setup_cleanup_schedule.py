from django.core.management.base import BaseCommand
from django_celery_beat.models import IntervalSchedule
from django_celery_beat.models import PeriodicTask


class Command(BaseCommand):
    help = "Set up the scheduled cleanup task for fake users"

    def handle(self, *args, **options):
        # Create or get the interval schedule (every 15 minutes)
        interval, created = IntervalSchedule.objects.get_or_create(
            every=15,
            period=IntervalSchedule.MINUTES,
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created schedule: every {interval.every} {interval.period}",
                ),
            )
        else:
            self.stdout.write(
                f"Using existing schedule: every {interval.every} {interval.period}",
            )

        # Create or update the periodic task
        task_name = "guesstheracetrack.users.tasks.cleanup_fake_users"

        task, created = PeriodicTask.objects.get_or_create(
            name="Cleanup Fake Users",
            defaults={
                "task": task_name,
                "interval": interval,
                "enabled": True,
                "description": "Removes users who never logged in within 15 minutes",
            },
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(f"Created periodic task: {task.name}"),
            )
        else:
            # Update existing task to ensure it's enabled and using correct interval
            task.interval = interval
            task.enabled = True
            task.description = (
                "Removes fake users who never logged in within 15 minutes"
            )
            task.save()
            self.stdout.write(
                self.style.SUCCESS(f"Updated existing periodic task: {task.name}"),
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"'{task.name}' scheduled every {interval.every} {interval.period}",
            ),
        )

        # Show current status
        self.stdout.write(f"Task enabled: {task.enabled}")
        self.stdout.write(f"Last run: {task.last_run_at}")

        # Show the task details
        self.stdout.write(f"Task ID: {task.id}")
        self.stdout.write(f"Task name: {task.name}")
        self.stdout.write(f"Task function: {task.task}")
        self.stdout.write(f"Interval: every {interval.every} {interval.period}")
