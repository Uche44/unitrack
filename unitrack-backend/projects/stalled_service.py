from datetime import timedelta

from django.db.models import Max, Q
from django.utils import timezone

from .models import Project, Submission, SupervisorContact

DEFAULT_THRESHOLD_DAYS = 10
MIN_THRESHOLD_DAYS = 1
MAX_THRESHOLD_DAYS = 90


def _last_value(queryset, field):
    return queryset.aggregate(last=Max(field))["last"]


def _baseline_for_student(student):
    if student.date_joined:
        return student.date_joined
    return student.created_at


def _project_baseline(project):
    if project is None:
        return None
    return project.created_at or project.updated_at


def student_activity_summary(student, threshold_days=DEFAULT_THRESHOLD_DAYS):
    cutoff = timezone.now() - timedelta(days=threshold_days)
    project = Project.objects.filter(student=student).order_by("-created_at").first()
    last_submission = _last_value(
        Submission.objects.filter(project__student=student), "submitted_at"
    )
    last_contact = _last_value(
        SupervisorContact.objects.filter(student=student), "occurred_at"
    )

    # Fallback chain: submission > contact > project creation > (only if no project) assignment date
    candidates = [
        ("submission", last_submission),
        ("contact", last_contact),
        ("project", _project_baseline(project)),
    ]
    if project is None:
        # No project at all — student hasn't started; use date_joined as the only baseline
        candidates.append(("assignment", _baseline_for_student(student)))
    last_activity_type = None
    last_activity_at = None
    for source, when in candidates:
        if when and (last_activity_at is None or when > last_activity_at):
            last_activity_at = when
            last_activity_type = source

    is_stalled = bool(last_activity_at is None or last_activity_at < cutoff)

    if is_stalled:
        reason_codes = ["no_activity_within_threshold"]
        if last_submission is None:
            reason_codes.append("no_submissions")
        if last_contact is None:
            reason_codes.append("no_supervisor_contact")
        if project is None:
            reason_codes.append("no_project")
    else:
        reason_codes = []

    return {
        "student_id": student.id,
        "last_activity_at": last_activity_at,
        "last_activity_type": last_activity_type,
        "last_submission_at": last_submission,
        "last_contact_at": last_contact,
        "current_milestone": project.status if project else None,
        "is_stalled": is_stalled,
        "reason_codes": reason_codes,
    }


def _queryset_for_supervisor(supervisor):
    return supervisor.students_under_supervision.filter(role="student")


def _queryset_for_admin(admin_user):
    department = admin_user.department
    qs = (
        __import__("accounts").models.User.objects
        if False else None
    )
    from accounts.models import User as AccountUser

    qs = AccountUser.objects.filter(role="student")
    if department:
        qs = qs.filter(
            Q(supervisor__isnull=False) & Q(supervisor__department=department)
        )
    return qs


def list_stalled_students(caller, *, threshold_days=DEFAULT_THRESHOLD_DAYS, sort="days_inactive"):
    threshold_days = max(MIN_THRESHOLD_DAYS, min(int(threshold_days), MAX_THRESHOLD_DAYS))
    if caller.role == "supervisor":
        students = list(_queryset_for_supervisor(caller).select_related("supervisor"))
    elif caller.role == "admin":
        students = list(_queryset_for_admin(caller).select_related("supervisor"))
    else:
        return {"threshold_days": threshold_days, "results": []}

    now = timezone.now()
    summaries = []
    for student in students:
        summary = student_activity_summary(student, threshold_days=threshold_days)
        if not summary["is_stalled"]:
            continue
        last_at = summary["last_activity_at"]
        days_inactive = (now - last_at).days if last_at else None
        summary["days_inactive"] = days_inactive
        if student.supervisor_id:
            summary["supervisor_summary"] = {
                "id": student.supervisor_id,
                "full_name": student.supervisor.full_name,
                "staff_id": student.supervisor.staff_id,
            }
        summaries.append(summary)

    if sort == "days_inactive":
        summaries.sort(
            key=lambda item: (
                -(item["days_inactive"] or 0),
                item["student_id"],
            )
        )
    return {"threshold_days": threshold_days, "results": summaries}