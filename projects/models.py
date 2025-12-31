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

    # MILESTONE_CHOICES = (
    #     ('proposal', 'Proposal'),
    #     ('chapter_one', 'Chapter One'),
    #     ('chapter_two', 'Chapter Two'),
    #     ('conclusion', 'conclusion'),
    #     # ('chapter_three', 'Chapter Three'),
    #     # ('chapter_four', 'Chapter Four'),
    #     # ('chapter_five', 'Chapter Five'),
    # )
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='supervised_projects')
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
        # ('chapter_four', 'Chapter Four'),
        # ('chapter_five', 'Chapter Five'),
    )
 
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='submissions')
    milestone = models.CharField(max_length=50, choices=MILESTONE_CHOICES)
    file_url = models.URLField()
    version = models.PositiveIntegerField(default=1)
    comment = models.TextField(null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)