from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from .models import Project, Submission
from .serializers import ProjectSerializer, SubmissionSerializer

class ProjectViewSet(ReadOnlyModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == 'student':
            return Project.objects.filter(student=user)

        if user.role == 'supervisor':
            return Project.objects.filter(supervisor=user)

        if user.role == 'admin':
            return Project.objects.all()

        return Project.objects.none()


class SubmissionViewSet(ReadOnlyModelViewSet):
    serializer_class = SubmissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == 'student':
            return Submission.objects.filter(project__student=user)

        if user.role == 'supervisor':
            return Submission.objects.filter(project__supervisor=user)

        if user.role == 'admin':
            return Submission.objects.all()

        return Submission.objects.none()
