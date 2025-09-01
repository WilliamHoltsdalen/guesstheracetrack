from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from guesstheracetrack.users.models import User
from guesstheracetrack.users.tasks import cleanup_fake_users


class CleanupFakeUsersTaskTest(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create a verified user (has last_login)
        self.verified_user = User.objects.create_user(
            email="verified@example.com",
            name="Verified User",
            password="testpass123",  # noqa: S106
        )
        self.verified_user.last_login = timezone.now()
        self.verified_user.save()

        # Create a fake user (no last_login, recent registration)
        self.recent_fake_user = User.objects.create_user(
            email="recent_fake@example.com",
            name="Recent Fake User",
            password="testpass123",  # noqa: S106
        )

        # Create a fake user (no last_login, old registration)
        self.old_fake_user = User.objects.create_user(
            email="old_fake@example.com",
            name="Old Fake User",
            password="testpass123",  # noqa: S106
        )
        # Set date_joined to 20 minutes ago
        self.old_fake_user.date_joined = timezone.now() - timedelta(minutes=20)
        self.old_fake_user.save()

    def test_cleanup_fake_users_removes_old_unverified_users(self):
        """Test that the task removes users who haven't logged in within 15 minutes"""
        initial_count = User.objects.count()

        # Run the task
        result = cleanup_fake_users()

        # Check that only the old fake user was removed
        final_count = User.objects.count()
        assert final_count == initial_count - 1

        # Verify the old fake user is gone
        assert not User.objects.filter(email="old_fake@example.com").exists()

        # Verify other users are still there
        assert User.objects.filter(email="verified@example.com").exists()
        assert User.objects.filter(email="recent_fake@example.com").exists()

        # Check the result message
        assert "Deleted 1 fake users" in result

    def test_cleanup_fake_users_no_users_to_remove(self):
        """Test that the task doesn't remove users when none qualify"""
        # Remove the old fake user first
        self.old_fake_user.delete()

        initial_count = User.objects.count()

        # Run the task
        result = cleanup_fake_users()

        # No users should be removed
        final_count = User.objects.count()
        assert final_count == initial_count

        # Check the result message
        assert "No fake users found to clean up" in result

    def test_cleanup_fake_users_with_custom_timezone(self):
        """Test that the task works correctly with different timezones"""
        # This test ensures the timezone handling works correctly
        with patch("django.utils.timezone.now") as mock_now:
            # Mock current time to be 20 minutes after the old fake user registration
            mock_now.return_value = self.old_fake_user.date_joined + timedelta(
                minutes=20,
            )

            result = cleanup_fake_users()

            # Should find and remove the old fake user
            assert "Deleted 1 fake users" in result
