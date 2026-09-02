from django.db import models
from django.core.exceptions import ValidationError
from accounts.models import User, Tag

class ProjectSession(models.Model):
    session = models.CharField(max_length=20)
    duration = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Enforce a single "current/active" session at a time.
        if self.is_active:
            ProjectSession.objects.filter(is_active=True).exclude(pk=self.pk).update(
                is_active=False
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.session


class Project(models.Model):
    STATUS_CHOICES = (
        ('proposal_pending', 'Proposal Pending'),
        ('proposal_approved', 'Proposal Approved'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    )

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='supervised_projects')
    session = models.ForeignKey(
        ProjectSession,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='projects',
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='projects')
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50, 
    choices=STATUS_CHOICES, default='proposal_pending')
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Submission(models.Model):
    MILESTONE_CHOICES = (
        ('proposal', 'Proposal'),
        ('chapter_one', 'Chapter One'),
        ('chapter_two', 'Chapter Two'),
        ('final_report', 'Final Report'),
        # ('chapter_three', 'Chapter Three'),
    )

    EXTRACTION_CHOICES = (
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('empty', 'Empty'),
        ('too_large', 'Too Large'),
        ('error', 'Error'),
    )

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='submissions')
    milestone = models.CharField(max_length=50, choices=MILESTONE_CHOICES)
    file_url = models.URLField()
    version = models.PositiveIntegerField(default=1)
    previous = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='next_versions',
        help_text="The immediately preceding version of this project/milestone.",
    )
    comment = models.TextField(null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)
    rejection_comment = models.TextField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)
    extracted_text = models.TextField(blank=True, default='')
    extraction_status = models.CharField(
        max_length=20, choices=EXTRACTION_CHOICES, default='pending'
    )
    extraction_error = models.TextField(blank=True, default='')

    class Meta:
        unique_together = (('project', 'milestone', 'version'),)


class SupervisorContact(models.Model):
    CONTACT_TYPES = (
        ('meeting', 'Meeting'),
        ('message', 'Message'),
        ('email', 'Email'),
        ('other', 'Other'),
    )

    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='contacts'
    )
    supervisor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='contacts_logged'
    )
    session = models.ForeignKey(
        ProjectSession, on_delete=models.SET_NULL, null=True, blank=True
    )
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPES, default='message')
    note = models.TextField(blank=True, default='')
    occurred_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['supervisor', 'session']),
            models.Index(fields=['student']),
        ]


class SubmissionReview(models.Model):
    DECISION_CHOICES = (
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    submission = models.ForeignKey(
        Submission, on_delete=models.CASCADE, related_name='reviews'
    )
    reviewer = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='reviews_given'
    )
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES)
    feedback = models.TextField(blank=True, default='')
    reviewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['submission']),
            models.Index(fields=['reviewer']),
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Submission reviews are immutable.")
        super().save(*args, **kwargs)