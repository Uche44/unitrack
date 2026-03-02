import os
from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    help = "Create an admin user from environment variables (ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_FULL_NAME)"

    def handle(self, *args, **options):
        email = os.getenv("ADMIN_EMAIL")
        password = os.getenv("ADMIN_PASSWORD")
        full_name = os.getenv("ADMIN_FULL_NAME", "Admin")

        if not email or not password:
            self.stderr.write(
                self.style.ERROR(
                    "ADMIN_EMAIL and ADMIN_PASSWORD environment variables are required."
                )
            )
            return

        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f"Admin user with email '{email}' already exists. Skipping.")
            )
            return

        User.objects.create_superuser(
            email=email,
            password=password,
            full_name=full_name,
            role="admin",
        )

        self.stdout.write(self.style.SUCCESS(f"Admin user '{email}' created successfully."))
