"""Reusable test builders for accounts fixtures.

These helpers are intentionally plain modules (not ``test*`` modules) so the
Django test runner does not try to discover them as tests. They are imported
from ``tests.py`` in each app.
"""

from accounts.models import User


def create_user(*, role, full_name="Test User", email=None, **kwargs):
    index = User.objects.count()
    email = email or f"{role}-{index}@example.com"
    password = kwargs.pop("password", "pass-test-123")
    return User.objects.create_user(
        email=email, password=password, full_name=full_name, role=role, **kwargs
    )


def create_admin(**kwargs):
    full_name = kwargs.pop("full_name", "Admin User")
    return create_user(role="admin", full_name=full_name, **kwargs)


def create_supervisor(*, approved=True, **kwargs):
    return create_user(role="supervisor", is_approved=approved, **kwargs)


def create_student(*, assigned=False, supervisor=None, **kwargs):
    return create_user(
        role="student",
        is_assigned=assigned,
        supervisor=supervisor,
        **kwargs,
    )