# from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ProjectSessionSerializer, ProjectCreateSerializer,SubmissionCreateSerializer
from .models import ProjectSession, Project, Submission
from rest_framework.permissions import IsAuthenticated
from .utils.cloudinary_upload import upload_file_to_cloudinary

# project session
class ProjectSessionView(APIView):

    def get(self, request):
        sessions = ProjectSession.objects.all().order_by('-created_at')
        serializer = ProjectSessionSerializer(sessions, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ProjectSessionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Session created successfully", "data": serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# create project

class CreateProjectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if user.role != 'student':
            return Response(
                {"error": "Only students can create projects"},
                status=status.HTTP_403_FORBIDDEN
            )

        data = request.data.copy()
        data['student'] = user.id   

        serializer = ProjectCreateSerializer(data=data)

        if serializer.is_valid():
            project = serializer.save()
            return Response(
                {
                    "message": "Project created successfully",
                    "project": serializer.data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# createsubmission

class CreateSubmissionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SubmissionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Get project explicitly
        project = serializer.validated_data.pop('project', None)
        if not project:
            return Response({"error": "Project is required"}, status=status.HTTP_400_BAD_REQUEST)

        milestone = serializer.validated_data.pop('milestone')
        file = serializer.validated_data.pop('file', None)

        if not file:
            return Response({"error": "File is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Determine next version for this milestone
        last_submission = (
            Submission.objects.filter(project=project, milestone=milestone)
            .order_by('-version')
            .first()
        )
        next_version = last_submission.version + 1 if last_submission else 1

        try:
            # Upload file to Cloudinary
            file_url = upload_file_to_cloudinary(file)
        except Exception as e:
            return Response({"error": f"File upload failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Create submission
        submission = Submission.objects.create(
            project=project,
            milestone=milestone,
            version=next_version,
            file_url=file_url,
            **serializer.validated_data
        )

        return Response(
            {
                "message": "Submission uploaded successfully",
                "data": {
                    "id": submission.id,
                    "milestone": submission.milestone,
                    "version": submission.version,
                    "file_url": submission.file_url,
                    "submitted_at": submission.submitted_at,
                }
            },
            status=status.HTTP_201_CREATED,
        )

class SupervisorStudentProjectView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        if request.user.role != 'supervisor':
            return Response(
                {"error": "Only supervisors can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )

        project = (
            Project.objects
            .filter(student_id=student_id, supervisor=request.user)
            .select_related("student", "supervisor")
            .prefetch_related("submissions")
            .first()
        )

        if not project:
            return Response(
                {"error": "Project not found or you are not assigned to this student"},
                status=status.HTTP_404_NOT_FOUND
            )

        from .serializers import ProjectDetailSerializer
        serializer = ProjectDetailSerializer(project)
        return Response(serializer.data)
