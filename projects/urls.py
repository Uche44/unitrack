from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import ProjectSessionView, CreateProjectView, CreateSubmissionView, SupervisorStudentProjectView
from .viewsets import ProjectViewSet, SubmissionViewSet

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='projects')
router.register(r'submissions', SubmissionViewSet, basename='submissions')

urlpatterns = [
    # Use a different path structure to avoid router conflicts
    path("supervisor/student/<int:student_id>/project/", SupervisorStudentProjectView.as_view(), name="supervisor-student-project"),
    path("projects/session/", ProjectSessionView.as_view(), name="project-session"),
    path("projects/create/", CreateProjectView.as_view(), name="create-project"),
    path("submissions/create/", CreateSubmissionView.as_view(), name="create-submission"),
]

urlpatterns += router.urls
