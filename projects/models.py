from django.db import models
from accounts.models import User

class ProjectSession(models.Model):
    session = models.CharField(max_length=20)
    duration = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.session


class Project(models.Model):
    STATUS_CHOICES = (
        ('proposal_pending', 'Proposal Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    )
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='supervised_projects')
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='proposal_pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
