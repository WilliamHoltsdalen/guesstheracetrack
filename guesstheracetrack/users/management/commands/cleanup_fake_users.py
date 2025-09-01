from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from guesstheracetrack.users.models import User


class Command(BaseCommand):
    help = "Clean up fake users who haven't logged in within 15 minutes of registration"

    def add_arguments(self, parser):
        parser.add_argument(
            "--minutes",
            type=int,
            default=15,
            help="Minutes after registration to consider a user fake (default: 15)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )

    def handle(self, *args, **options):
        minutes = options["minutes"]
        dry_run = options["dry_run"]

        cutoff_time = timezone.now() - timedelta(minutes=minutes)

        fake_users = User.objects.filter(
            last_login__isnull=True,
            date_joined__lt=cutoff_time,
        )

        count = fake_users.count()

        if count == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"No fake users found (registered before {cutoff_time})",
                ),
            )
            return

        self.stdout.write(
            f"Found {count} fake users registered before {cutoff_time}",
        )

        display_limit = 10
        if dry_run:
            self.stdout.write("DRY RUN - Would delete the following users:")
            for user in fake_users[:display_limit]:  # Show first 10
                self.stdout.write(f"  - {user.email} (registered: {user.date_joined})")
            if count > display_limit:
                self.stdout.write(f"  ... and {count - display_limit} more")
        else:
            self.stdout.write("Deleting the following users:")
            for user in fake_users[:display_limit]:  # Show first 10
                self.stdout.write(f"  - {user.email} (registered: {user.date_joined})")
            if count > display_limit:
                self.stdout.write(f"  ... and {count - display_limit} more")

            confirm = input(
                f"\nAre you sure you want to delete {count} users? (yes/no): ",
            )
            if confirm.lower() in ["yes", "y"]:
                fake_users.delete()
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully deleted {count} fake users"),
                )
            else:
                self.stdout.write("Operation cancelled")
