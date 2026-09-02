
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class Tag(models.Model):
    """A normalized research/topic or expertise tag shared by projects
    (topic tags) and supervisors (expertise tags)."""

    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('supervisor', 'Supervisor'),
        ('admin', 'Admin'),
    )
    username = None 
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    department = models.CharField(max_length=100, null=True, blank=True)
    matric_no = models.CharField(max_length=20, unique=True, null=True, blank=True)
    staff_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    is_approved = models.BooleanField(default=True)  # default for students
    is_assigned = models.BooleanField(default=False, null=True, blank=True)
    is_fully_booked = models.BooleanField(default=False, null=True, blank=True) #for supervisor
    benchmark_opt_in = models.BooleanField(default=False)
    areas_of_expertise = models.CharField(max_length=500, blank=True, default="")
    project_interests = models.CharField(max_length=500, blank=True, default="")
    # explicit positive capacity; capacity decisions derive workload from this
    capacity = models.PositiveIntegerField(default=5)
    expertise_tags = models.ManyToManyField(
        Tag, blank=True, related_name='supervisors'
    )
    # is_guest = models.BooleanField(default=False)
    supervisor = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students_under_supervision'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    @property
    def current_load(self):
        if self.role != 'supervisor':
            return 0
        return self.students_under_supervision.count()

    @property
    def remaining_capacity(self):
        if self.role != 'supervisor':
            return 0
        return max(self.capacity - self.current_load, 0)




