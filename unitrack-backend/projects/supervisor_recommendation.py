import re

from django.db.models import Q

from accounts.models import User
from .models import ProjectSession


EXPERTISE_WEIGHT = 60
WORKLOAD_WEIGHT = 30
CAPACITY_WEIGHT = 10


def _split_tags(text):
    if not text:
        return set()
    return {
        token.strip().lower()
        for token in re.split(r"[,;\n]+", text)
        if token.strip()
    }


def resolve_active_session():
    return (
        ProjectSession.objects.filter(is_active=True).order_by("-created_at").first()
        or ProjectSession.objects.order_by("-created_at").first()
    )


def score_candidate(supervisor, student_interests):
    expertise_keywords = _split_tags(supervisor.areas_of_expertise)
    interests = _split_tags(student_interests)
    overlap = expertise_keywords & interests
    overlap_ratio = (
        len(overlap) / max(len(interests), 1) if interests else 0
    )

    workload_count = supervisor.students_under_supervision.filter(role="student").count()
    capacity = max(int(supervisor.capacity or 0), 1)
    workload_ratio = workload_count / capacity

    remaining_capacity = max(capacity - workload_count, 0)
    remaining_ratio = remaining_capacity / capacity

    expertise_score = round(overlap_ratio * EXPERTISE_WEIGHT, 2)
    workload_score = round(max(0.0, 1.0 - workload_ratio) * WORKLOAD_WEIGHT, 2)
    capacity_score = round(remaining_ratio * CAPACITY_WEIGHT, 2)
    total = round(expertise_score + workload_score + capacity_score, 2)

    if overlap:
        expertise_summary = (
            f"Dr. {supervisor.full_name.split()[-1]} lists "
            + ", ".join(sorted(expertise_keywords))
            + f"; student interest is {student_interests}; matched on "
            + ", ".join(sorted(overlap))
            + "."
        )
    elif interests:
        expertise_summary = (
            f"Dr. {supervisor.full_name.split()[-1]} lists "
            + (", ".join(sorted(expertise_keywords)) or "no expertise tags")
            + f"; student interest is {student_interests}; no tag overlap."
        )
    else:
        expertise_summary = (
            f"Dr. {supervisor.full_name.split()[-1]} lists "
            + (", ".join(sorted(expertise_keywords)) or "no expertise tags")
            + "; student has not declared project interests."
        )

    reason_facts = [
        expertise_summary,
        f"Current load {workload_count}/{capacity}; remaining capacity {remaining_capacity}.",
    ]

    return {
        "supervisor_id": supervisor.id,
        "full_name": supervisor.full_name,
        "staff_id": supervisor.staff_id,
        "department": supervisor.department,
        "areas_of_expertise": supervisor.areas_of_expertise or "",
        "matched_keywords": sorted(overlap),
        "current_load": workload_count,
        "capacity": capacity,
        "remaining_capacity": remaining_capacity,
        "expertise_score": expertise_score,
        "workload_score": workload_score,
        "capacity_score": capacity_score,
        "total_score": total,
        "reason_facts": reason_facts,
    }


def suggest_supervisors(student, *, limit=5, session=None):
    limit = min(max(int(limit), 1), 10)
    session = session or resolve_active_session()
    student_interests = student.project_interests or ""

    candidates = User.objects.filter(
        role="supervisor",
        is_approved=True,
        is_fully_booked=False,
    )
    if student.department:
        candidates = candidates.filter(
            Q(department__isnull=True) | Q(department=student.department)
        )

    scored = []
    for supervisor in candidates:
        if supervisor.remaining_capacity <= 0:
            continue
        scored.append(score_candidate(supervisor, student_interests))

    scored.sort(
        key=lambda item: (
            -item["total_score"],
            item["remaining_capacity"],
            -item["current_load"],
            item["supervisor_id"],
        )
    )

    return {
        "mode": "supervisor_for_student",
        "student": {
            "id": student.id,
            "full_name": student.full_name,
            "department": student.department,
            "project_interests": student.project_interests or "",
        },
        "session": getattr(session, "id", None),
        "candidates": scored[:limit],
        "excluded": [
            {
                "supervisor_id": s.id,
                "reason": "no_remaining_capacity",
                "full_name": s.full_name,
            }
            for s in candidates
            if s.remaining_capacity <= 0
        ],
        "result": "ok" if scored else "no_suitable_supervisor",
    }


def _score_student_for_supervisor(student, supervisor_expertise):
    keywords = _split_tags(student.project_interests)
    expertise = _split_tags(supervisor_expertise)
    overlap = expertise & keywords
    overlap_ratio = len(overlap) / max(len(expertise), 1) if expertise else 0
    expertise_score = round(overlap_ratio * 60, 2)

    if overlap:
        reasoning = (
            f" { 'Supervisor'} lists "
            + ", ".join(sorted(expertise))
            + f"; Student, {student.full_name.split()[-1]} lists "
            + (student.project_interests or "(no interests)")
            + "; Matched on "
            + ", ".join(sorted(overlap))
            + "."
        )
    elif keywords:
        reasoning = (
            f"Student {student.full_name} declared "
            + student.project_interests
            + "; supervisor expertise is "
            + (supervisor_expertise or "(blank)")
            + "; no tag overlap."
        )
    else:
        reasoning = (
            f"Student {student.full_name} has not declared project interests."
        )

    return {
        "student_id": student.id,
        "full_name": student.full_name,
        "matric_no": student.matric_no,
        "department": student.department,
        "project_interests": student.project_interests or "",
        "interest_keywords": sorted(keywords),
        "matched_keywords": sorted(overlap),
        "expertise_score": expertise_score,
        "reasoning": reasoning,
    }


def suggest_students_for_supervisor(supervisor, *, limit=5, session=None):
    limit = min(max(int(limit), 1), 10)
    session = session or resolve_active_session()
    expertise = supervisor.areas_of_expertise or ""

    students = User.objects.filter(
        role="student",
        is_assigned=False,
    )
    if supervisor.department:
        students = students.filter(
            Q(department__isnull=True) | Q(department=supervisor.department)
        )
    students = students.distinct()

    scored = [_score_student_for_supervisor(student, expertise) for student in students]
    scored.sort(
        key=lambda item: (
            -item["expertise_score"],
            item["student_id"],
        )
    )

    return {
        "mode": "students_for_supervisor",
        "supervisor": {
            "id": supervisor.id,
            "full_name": supervisor.full_name,
            "department": supervisor.department,
            "areas_of_expertise": supervisor.areas_of_expertise or "",
        },
        "session": getattr(session, "id", None),
        "candidates": scored[:limit],
        "result": "ok" if scored else "no_suitable_students",
    }