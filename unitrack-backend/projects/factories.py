"""Reusable test builders for project/submission fixtures."""

from datetime import timedelta

from django.utils import timezone

from projects.models import (
    Project,
    ProjectSession,
    Submission,
    SupervisorContact,
    SubmissionReview,
)


def create_session(
    session="2025/2026",
    duration="12 months",
    start_date=None,
    end_date=None,
    is_active=False,
    **kwargs,
):
    start_date = start_date or timezone.localdate()
    end_date = end_date or (start_date + timedelta(days=365))
    return ProjectSession.objects.create(
        session=session,
        duration=duration,
        start_date=start_date,
        end_date=end_date,
        is_active=is_active,
        **kwargs,
    )


def create_project(
    *,
    student,
    supervisor=None,
    session=None,
    title="Sample Project",
    tags=None,
    **kwargs,
):
    kwargs.setdefault("status", "proposal_pending")
    project = Project.objects.create(
        student=student,
        supervisor=supervisor,
        session=session,
        title=title,
        **kwargs,
    )
    if tags:
        project.tags.set(tags)
    return project


def create_submission(
    *,
    project,
    milestone="proposal",
    version=1,
    file_url="https://cdn.example.com/sub.pdf",
    previous=None,
    extracted_text="",
    extraction_status="pending",
    **kwargs,
):
    return Submission.objects.create(
        project=project,
        milestone=milestone,
        version=version,
        file_url=file_url,
        previous=previous,
        extracted_text=extracted_text,
        extraction_status=extraction_status,
        **kwargs,
    )


def create_contact(
    *,
    student,
    supervisor,
    session=None,
    contact_type="message",
    note="",
    occurred_at=None,
    **kwargs,
):
    occurred_at = occurred_at or timezone.now()
    return SupervisorContact.objects.create(
        student=student,
        supervisor=supervisor,
        session=session,
        contact_type=contact_type,
        note=note,
        occurred_at=occurred_at,
        **kwargs,
    )


def create_review(
    *,
    submission,
    reviewer,
    decision="approved",
    feedback="",
    **kwargs,
):
    return SubmissionReview.objects.create(
        submission=submission,
        reviewer=reviewer,
        decision=decision,
        feedback=feedback,
        **kwargs,
    )