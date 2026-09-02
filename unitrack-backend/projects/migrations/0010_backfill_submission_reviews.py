from django.db import migrations


def backfill_submission_reviews(apps, schema_editor):
    """Derive SubmissionReview rows from existing submission flags.

    Only approved/rejected submissions without an existing review are
    considered. The reviewer is the project's supervisor; feedback is the
    stored rejection comment. Nothing is fabricated: submissions without a
    decision, and rows without an identifiable reviewer, are skipped.
    """
    Submission = apps.get_model('projects', 'Submission')
    SubmissionReview = apps.get_model('projects', 'SubmissionReview')

    for submission in Submission.objects.select_related('project'):
        if SubmissionReview.objects.filter(submission=submission).exists():
            continue

        if submission.is_approved:
            decision, feedback = 'approved', ''
        elif submission.is_rejected:
            decision = 'rejected'
            feedback = submission.rejection_comment or ''
        else:
            continue

        reviewer_id = submission.project.supervisor_id
        if reviewer_id is None:
            continue

        SubmissionReview.objects.create(
            submission=submission,
            reviewer_id=reviewer_id,
            decision=decision,
            feedback=feedback,
        )


def keep_backfilled_reviews(apps, schema_editor):
    """Reviews are immutable derived records; the backfill is not reversible."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0009_backfill_project_session'),
    ]

    operations = [
        migrations.RunPython(backfill_submission_reviews, keep_backfilled_reviews),
    ]
