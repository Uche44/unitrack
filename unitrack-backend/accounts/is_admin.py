from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework import status

class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "admin")


