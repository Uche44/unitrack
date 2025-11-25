from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework import status

class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "admin")


class IsNotGuest(BasePermission):
    """
    Permission to block guest users from performing write operations.
    """
    message = "Guest users cannot perform this action."

    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            if request.user.is_guest and request.method not in ['GET', 'HEAD', 'OPTIONS']:
                return False
        return True


class GuestReadOnly(BasePermission):
    """
    Permission to allow guests read-only access.
    """
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            if request.user.is_guest and request.method not in ['GET', 'HEAD', 'OPTIONS']:
                return False
        return True

