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



class CreateProjectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if user.role != 'student':
            return Response(
                {"error": "Only students can create projects"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if student has a supervisor assigned
        if not hasattr(user, 'supervisor') or user.supervisor is None:
            return Response(
                {"error": "You must have a supervisor assigned before creating a project"},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = request.data.copy()
        data['student'] = user.id
        data['supervisor'] = user.supervisor.id  

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
        # Debug logging
        print(f"🔍 DEBUG: Logged in user: {request.user.id} - {request.user.email}")
        print(f"🔍 DEBUG: User role: {request.user.role}")
        print(f"🔍 DEBUG: Looking for student_id: {student_id}")
        
        if request.user.role != 'supervisor':
            return Response(
                {"error": "Only supervisors can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if ANY project exists for this student
        all_projects = Project.objects.filter(student_id=student_id)
        print(f"🔍 DEBUG: Projects found for student {student_id}: {all_projects.count()}")
        for p in all_projects:
            print(f"   - Project {p.id}: supervisor_id={p.supervisor_id}, student_id={p.student_id}")

        project = (
            Project.objects
            .filter(student_id=student_id, supervisor=request.user)
            .select_related("student", "supervisor")
            .prefetch_related("submissions")
            .first()
        )

        print(f"🔍 DEBUG: Project found for current supervisor: {project}")

        if not project:
            return Response(
                {"error": "Project not found or you are not assigned to this student"},
                status=status.HTTP_404_NOT_FOUND
            )

        from .serializers import ProjectDetailSerializer
        serializer = ProjectDetailSerializer(project)
        return Response(serializer.data)


class ApproveRejectProposalView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
       
        user = request.user

        # Verify user is a supervisor
        if user.role != 'supervisor':
            return Response(
                {"error": "Only supervisors can approve or reject proposals"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get the project
        try:
            project = Project.objects.select_related('student', 'supervisor').get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {"error": "Project not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verify the supervisor is assigned to this project
        if project.supervisor != user:
            return Response(
                {"error": "You are not assigned to this project"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate request data
        from .serializers import ProposalActionSerializer
        serializer = ProposalActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        action = serializer.validated_data['action']
        comment = serializer.validated_data.get('comment', '')

        # Get the latest proposal submission
        latest_proposal = (
            Submission.objects
            .filter(project=project, milestone='proposal')
            .order_by('-version')
            .first()
        )

        if not latest_proposal:
            return Response(
                {"error": "No proposal submission found for this project"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Perform the action
        if action == 'approve':
            latest_proposal.is_approved = True
            latest_proposal.is_rejected = False
            latest_proposal.rejection_comment = None
            latest_proposal.save()

            # Update project status
            project.status = 'proposal_approved'
            project.is_approved = True
            project.save()

            return Response({
                "message": "Proposal approved successfully",
                "project": {
                    "id": project.id,
                    "status": project.status,
                    "is_approved": project.is_approved
                }
            }, status=status.HTTP_200_OK)

        elif action == 'reject':
            latest_proposal.is_approved = False
            latest_proposal.is_rejected = True
            latest_proposal.rejection_comment = comment
            latest_proposal.save()

            # Keep project status as proposal_pending
            project.status = 'proposal_pending'
            project.is_approved = False
            project.save()

            return Response({
                "message": "Proposal rejected",
                "project": {
                    "id": project.id,
                    "status": project.status,
                    "is_approved": project.is_approved
                },
                "rejection_comment": comment
            }, status=status.HTTP_200_OK)