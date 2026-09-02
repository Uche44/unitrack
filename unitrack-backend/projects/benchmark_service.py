from collections import Counter

from django.db.models import Q

from accounts.models import User
from .models import Project, ProjectSession


STAGE_ORDER = (
    "no_project",
    "proposal_pending",
    "proposal_approved",
    "in_progress",
    "completed",
)

STAGE_LABELS = {
    "no_project": "No project",
    "proposal_pending": "Proposal pending",
    "proposal_approved": "Proposal approved",
    "in_progress": "In progress",
    "completed": "Completed",
}

MIN_COHORT_SIZE = 5


def resolve_active_session():
    return (
        ProjectSession.objects.filter(is_active=True).order_by("-created_at").first()
        or ProjectSession.objects.order_by("-created_at").first()
    )


def _stage_for(student):
    project = (
        Project.objects.filter(student=student).order_by("-created_at").first()
    )
    if project is None:
        return "no_project"
    if project.status == "proposal_pending":
        return "proposal_pending"
    if project.status == "completed":
        return "completed"
    if project.status == "proposal_approved":
        return "proposal_approved"
    return "in_progress"


def cohort_for(student, session):
    qs = User.objects.filter(role="student")
    if student.department:
        qs = qs.filter(department=student.department)
    if session is not None:
        qs = qs.filter(
            Q(supervisor__isnull=True)
            | Q(supervisor__isnull=False) & Q(supervisor__id__isnull=False)
        )
    return qs.distinct()


def build_cohort_benchmark(student):
    if not student.benchmark_opt_in:
        return {
            "opted_in": False,
            "suppressed_reason": "opt_out",
            "minimum_cohort_size": MIN_COHORT_SIZE,
            "stage_order": list(STAGE_ORDER),
            "stage_labels": STAGE_LABELS,
        }

    session = resolve_active_session()
    members = list(cohort_for(student, session))
    total = len(members)
    if total < MIN_COHORT_SIZE:
        return {
            "opted_in": True,
            "suppressed_reason": "minimum_cohort_not_met",
            "minimum_cohort_size": MIN_COHORT_SIZE,
            "cohort_size": total,
            "stage_order": list(STAGE_ORDER),
            "stage_labels": STAGE_LABELS,
        }

    stages = Counter(_stage_for(member) for member in members)
    aggregate = {}
    for stage in STAGE_ORDER:
        count = stages.get(stage, 0)
        aggregate[stage] = {
            "count": count,
            "percentage": round((count / total) * 100, 2),
        }

    cumulative = {}
    running = 0
    for stage in reversed(STAGE_ORDER):
        running += aggregate[stage]["count"]
        cumulative[stage] = {
            "count": running,
            "percentage": round((running / total) * 100, 2),
        }

    stage_ranks = {stage: index for index, stage in enumerate(STAGE_ORDER)}
    ordinals = sorted(stage_ranks[_stage_for(member)] for member in members)
    median_index = (len(ordinals) - 1) // 2
    median_stage = STAGE_ORDER[ordinals[median_index]]

    caller_stage = _stage_for(student)
    below_or_equal = sum(1 for ordinal in ordinals if ordinal <= stage_ranks[caller_stage])
    percentile = round((below_or_equal / total) * 100, 2)
    band = (
        "bottom_third" if percentile < 34
        else "middle_third" if percentile < 67
        else "top_third"
    )

    return {
        "opted_in": True,
        "suppressed_reason": None,
        "minimum_cohort_size": MIN_COHORT_SIZE,
        "cohort_size": total,
        "session": getattr(session, "id", None),
        "caller_stage": caller_stage,
        "caller_percentile": percentile,
        "caller_band": band,
        "median_stage": median_stage,
        "aggregate": aggregate,
        "cumulative": cumulative,
        "stage_order": list(STAGE_ORDER),
        "stage_labels": STAGE_LABELS,
    }