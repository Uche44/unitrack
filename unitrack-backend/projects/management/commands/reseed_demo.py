"""Reset demo accounts and re-run the seed.

Removes the previously seeded demo users (admin/supervisor/student +
extras) so the new Computer Science cohort takes their place, then runs
`seed_demo` for you. Idempotent: running again is a no-op if no demo users
exist.
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand

from accounts.models import User
from projects.models import SubmissionReview, SupervisorContact


LEGACY_DEMO_EMAILS = [
    "admin-demo@example.com",
    "supervisor-demo@example.com",
    "student-demo@example.com",
]
LEGACY_DEMO_PREFIXES = (
    "supervisor-robotics@",
    "supervisor-data@",
    "supervisor-full@",
    "student-active-",
    "student-stalled-",
    "unassigned-",
)


class Command(BaseCommand):
    help = "Wipe prior demo users and re-seed the Computer Science demo dataset."

    def handle(self, *args, **options):
        legacy_users = User.objects.filter(email__in=LEGACY_DEMO_EMAILS)
        for prefix in LEGACY_DEMO_PREFIXES:
            legacy_users |= User.objects.filter(email__startswith=prefix)
        legacy_users = legacy_users.distinct()

        # Unlink protected references so legacy users can be deleted.
        SubmissionReview.objects.filter(reviewer__in=legacy_users).delete()
        SupervisorContact.objects.filter(supervisor__in=legacy_users).delete()

        count = legacy_users.count()
        legacy_users.delete()
        self.stdout.write(self.style.WARNING(
            f"Removed {count} legacy demo account(s)."
        ))
        call_command("seed_demo")

