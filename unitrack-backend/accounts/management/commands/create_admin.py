from django.core.management.base import BaseCommand
from accounts.serializers import UserSerializer
from accounts.models import User
import getpass

class Command(BaseCommand):
    help = "Create an application admin using safe interactive input"

    def handle(self, *args, **kwargs):
        if User.objects.filter(role="admin").exists():
            self.stdout.write(self.style.WARNING("Admin already exists"))
            return

       
        email = input("Admin Email: ")
        # full_name = input("Full Name: ")
        staff_id = input("staff id: ") 
        password = getpass.getpass("Password (hidden): ")

        data = {
            # "full_name": full_name,
            "full_name": "Admin",
            "email": email,
            "password": password,
            "role": "admin",
            "staff_id": staff_id,
            # "is_approved": True,
        }

        serializer = UserSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.stdout.write(self.style.SUCCESS("Admin user created!"))
