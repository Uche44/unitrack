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
        
        # Enforce sequential submission order
        # proposal -> chapter_one -> chapter_two -> final_report
        
        if milestone == 'chapter_one':
             # Check if proposal is approved
            proposal = Submission.objects.filter(project=project, milestone='proposal', is_approved=True).exists()
            if not proposal:
                return Response({"error": "Proposal must be approved before submitting Chapter One"}, status=status.HTTP_400_BAD_REQUEST)
        
        elif milestone == 'chapter_two':
            # Check if chapter_one is approved
            chapter_one = Submission.objects.filter(project=project, milestone='chapter_one', is_approved=True).exists()
            if not chapter_one:
                 return Response({"error": "Chapter One must be approved before submitting Chapter Two"}, status=status.HTTP_400_BAD_REQUEST)
        
        elif milestone == 'final_report':
            # Check if chapter_two is approved
            chapter_two = Submission.objects.filter(project=project, milestone='chapter_two', is_approved=True).exists()
            if not chapter_two:
                 return Response({"error": "Chapter Two must be approved before submitting Final Report"}, status=status.HTTP_400_BAD_REQUEST)


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

        # Get the LATEST project for this student (ordered by creation date)
        project = (
            Project.objects
            .filter(student_id=student_id, supervisor=request.user)
            .select_related("student", "supervisor")
            .prefetch_related("submissions")
            .order_by('-created_at')  # Get the most recent project
            .first()
        )

        print(f"🔍 DEBUG: Latest project found for current supervisor: {project}")

        if not project:
            return Response(
                {"error": "Project not found or you are not assigned to this student"},
                status=status.HTTP_404_NOT_FOUND
            )



        from .serializers import ProjectDetailSerializer
        serializer = ProjectDetailSerializer(project)
        return Response(serializer.data)


class ApproveRejectSubmissionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, submission_id):
       
        user = request.user

        # Verify user is a supervisor
        if user.role != 'supervisor':
            return Response(
                {"error": "Only supervisors can approve or reject submissions"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get the submission
        try:
            submission = Submission.objects.get(id=submission_id)
            project = submission.project
        except Submission.DoesNotExist:
            return Response(
                {"error": "Submission not found"},
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

        # Perform the action
        if action == 'approve':
            submission.is_approved = True
            submission.is_rejected = False
            submission.rejection_comment = None
            submission.save()

            # Update project status based on milestone
            if submission.milestone == 'proposal':
                project.status = 'proposal_approved'
                project.is_approved = True
            elif submission.milestone == 'final_report':
                project.status = 'completed'
            # else: for chapter_one and chapter_two, we might keep it as 'in_progress' or 'proposal_approved'
            # Let's set it to 'in_progress' if it's past proposal
            elif submission.milestone in ['chapter_one', 'chapter_two']:
                project.status = 'in_progress'
            
            project.save()

            return Response({
                "message": "Submission approved successfully",
                "project": {
                    "id": project.id,
                    "status": project.status,
                    "is_approved": project.is_approved
                }
            }, status=status.HTTP_200_OK)

        elif action == 'reject':
            submission.is_approved = False
            submission.is_rejected = True
            submission.rejection_comment = comment
            submission.save()

            # If proposal is rejected, reset project status
            if submission.milestone == 'proposal':
                project.status = 'proposal_pending'
                project.is_approved = False
                project.save()

            return Response({
                "message": "Submission rejected",
                "project": {
                    "id": project.id,
                    "status": project.status,
                    "is_approved": project.is_approved
                },
                "rejection_comment": comment
            }, status=status.HTTP_200_OK)


import requests
import io
from pypdf import PdfWriter
from django.http import HttpResponse

class DownloadFullReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
             return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)

        # Ensure user has access
        if request.user.role == 'student' and project.student != request.user:
             return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
        if request.user.role == 'supervisor' and project.supervisor != request.user:
             return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        # Check if project deemed complete or specifically check final report approval
        # We'll just check if there are approved submissions for all stages, or at least some.
        # But user asked for "after final report is approved".
        
        # We can also just fetch all approved submissions in order.
        milestones_order = ['proposal', 'chapter_one', 'chapter_two', 'final_report']
        
        approved_submissions = []
        for milestone in milestones_order:
            # Get latest approved submission for this milestone
            sub = Submission.objects.filter(
                project=project, 
                milestone=milestone, 
                is_approved=True
            ).order_by('-version').first()
            
            if sub:
                approved_submissions.append(sub)
        
        if not approved_submissions:
             return Response({"error": "No approved submissions found"}, status=status.HTTP_404_NOT_FOUND)

        # Merge PDFs
        merger = PdfWriter()
        
        for sub in approved_submissions:
            if not sub.file_url:
                continue
                
            try:
                response = requests.get(sub.file_url)
                if response.status_code == 200:
                    pdf_content = io.BytesIO(response.content)
                    merger.append(pdf_content)
            except Exception as e:
                print(f"Error downloading file {sub.file_url}: {e}")
                # Continue or fail? Let's continue and try to merge what we have.

        output_buffer = io.BytesIO()
        merger.write(output_buffer)
        merger.close()
        
        output_buffer.seek(0)
        
        filename = f"{project.title.replace(' ', '_')}_Full_Report.pdf"
        
        response = HttpResponse(output_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response