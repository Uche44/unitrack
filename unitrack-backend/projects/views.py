# from django.shortcuts import render
from django.db import transaction, IntegrityError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    ProjectSessionSerializer,
    ProjectCreateSerializer,
    SubmissionCreateSerializer,
    SupervisorContactCreateSerializer,
    SupervisorContactSerializer,
    SubmissionReviewSerializer,
)
from .models import ProjectSession, Project, Submission, SupervisorContact, SubmissionReview
from accounts.models import User
from .feedback_themes import analyze_feedback_themes, resolve_feedback_session
from .diff_service import (
    compute_diff,
    evaluate_feedback_coverage,
    normalize_text,
    split_paragraphs,
)
from .stalled_service import list_stalled_students
from .supervisor_recommendation import suggest_supervisors
from .defense_service import (
    CATEGORY_LABELS,
    DIFFICULTY_LEVELS,
    build_defense_seeds,
)
from .benchmark_service import build_cohort_benchmark
from .supervisor_recommendation import (
    score_candidate,
    suggest_students_for_supervisor,
    suggest_supervisors,
    _split_tags,
)
from rest_framework.permissions import IsAuthenticated
from accounts.is_admin import IsAdminRole
from .utils.cloudinary_upload import upload_file_to_cloudinary
from .utils.pdf_text import extract_pdf_text


def resolve_project_session():
    """Return the active session if any, else the most recently created one."""
    active = ProjectSession.objects.filter(is_active=True).order_by('-created_at').first()
    if active:
        return active
    return ProjectSession.objects.order_by('-created_at').first()

# project session
class ProjectSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminRole()]
        return super().get_permissions()

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
        session = resolve_project_session()
        if session is not None:
            data['session'] = session.id

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
        user = request.user

        # Only students may submit files.
        if user.role != 'student':
            return Response(
                {"error": "Only students can submit files"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Resolve and verify project ownership before doing any expensive work.
        project_id = request.data.get("project")
        try:
            project = Project.objects.get(id=project_id)
        except (Project.DoesNotExist, TypeError, ValueError):
            return Response(
                {"error": "Project is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if project.student != user:
            return Response(
                {"error": "You can only submit files to your own project"},
                status=status.HTTP_403_FORBIDDEN,
            )

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


        # Extract text (bounded) and allocate the next version transactionally.
        text, ext_status, ext_error = extract_pdf_text(file)
        file.seek(0)

        with transaction.atomic():
            last_submission = (
                Submission.objects.filter(project=project, milestone=milestone)
                .order_by('-version')
                .first()
            )
            next_version = last_submission.version + 1 if last_submission else 1

            try:
                file_url = upload_file_to_cloudinary(file)
            except Exception as e:  # noqa: BLE001 - report upload failure cleanly
                return Response(
                    {"error": f"File upload failed: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            try:
                submission = Submission.objects.create(
                    project=project,
                    milestone=milestone,
                    version=next_version,
                    previous=last_submission,
                    file_url=file_url,
                    extracted_text=text,
                    extraction_status=ext_status,
                    extraction_error=ext_error,
                    **serializer.validated_data
                )
            except IntegrityError:
                return Response(
                    {"error": "A submission with this version already exists. Please retry."},
                    status=status.HTTP_409_CONFLICT,
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
                    "extraction_status": submission.extraction_status,
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

    @transaction.atomic
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

            SubmissionReview.objects.create(
                submission=submission,
                reviewer=user,
                decision='approved',
                feedback=comment or '',
            )

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

            SubmissionReview.objects.create(
                submission=submission,
                reviewer=user,
                decision='rejected',
                feedback=comment or '',
            )

            return Response({
                "message": "Submission rejected",
                "project": {
                    "id": project.id,
                    "status": project.status,
                    "is_approved": project.is_approved
                },
                "rejection_comment": comment
            }, status=status.HTTP_200_OK)


class SupervisorContactView(APIView):
    permission_classes = [IsAuthenticated]

    def _require_supervisor(self, request):
        if request.user.role != 'supervisor':
            return None
        return request.user

    def get(self, request):
        supervisor = self._require_supervisor(request)
        if supervisor is None:
            return Response(
                {"error": "Only supervisors can view contact logs"},
                status=status.HTTP_403_FORBIDDEN,
            )
        contacts = (
            SupervisorContact.objects.filter(supervisor=supervisor)
            .select_related('student', 'session')
            .order_by('-occurred_at')
        )
        return Response(SupervisorContactSerializer(contacts, many=True).data)

    def post(self, request):
        supervisor = self._require_supervisor(request)
        if supervisor is None:
            return Response(
                {"error": "Only supervisors can log contacts"},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = SupervisorContactCreateSerializer(
            data=request.data, context={'supervisor': supervisor}
        )
        if serializer.is_valid():
            contact = serializer.save()
            return Response(
                SupervisorContactSerializer(contact).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FeedbackThemesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'supervisor':
            return Response(
                {"error": "Only supervisors can view feedback themes"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            min_occurrences = int(request.query_params.get('min_occurrences', 2))
            limit = int(request.query_params.get('limit', 5))
        except (TypeError, ValueError):
            return Response(
                {"error": "min_occurrences and limit must be integers"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if min_occurrences < 1 or limit < 1 or limit > 7:
            return Response(
                {"error": "min_occurrences must be at least 1 and limit must be between 1 and 7"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        requested_session = request.query_params.get('session_id')
        session = resolve_feedback_session(requested_session, resolve_project_session())
        if session is None:
            return Response({
                "session": None,
                "total_reviews": 0,
                "total_submissions": 0,
                "total_students": 0,
                "themes": [],
            })

        reviews = SubmissionReview.objects.filter(
            submission__project__supervisor=request.user,
            submission__project__session=session,
        )
        result = analyze_feedback_themes(
            reviews,
            min_occurrences=min_occurrences,
            limit=limit,
        )
        return Response({"session": session.id, **result})


class SupervisorWorkloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'admin':
            return Response(
                {"error": "Only admins can view supervisor workload"},
                status=status.HTTP_403_FORBIDDEN,
            )
        supervisors = User.objects.filter(role="supervisor").order_by("id")
        return Response([
            {
                "supervisor_id": s.id,
                "full_name": s.full_name,
                "staff_id": s.staff_id,
                "department": s.department,
                "areas_of_expertise": s.areas_of_expertise or "",
                "expertise_keywords": sorted(_split_tags(s.areas_of_expertise)),
                "current_load": s.current_load,
                "capacity": s.capacity,
                "remaining_capacity": s.remaining_capacity,
                "is_fully_booked": bool(s.is_fully_booked),
                "is_approved": bool(s.is_approved),
            }
            for s in supervisors
        ])


class StudentInterestsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'admin':
            return Response(
                {"error": "Only admins can view student interests"},
                status=status.HTTP_403_FORBIDDEN,
            )
        students = User.objects.filter(role="student", is_assigned=False).order_by("id")
        return Response([
            {
                "student_id": s.id,
                "full_name": s.full_name,
                "matric_no": s.matric_no,
                "department": s.department,
                "project_interests": s.project_interests or "",
                "interest_keywords": sorted(_split_tags(s.project_interests)),
            }
            for s in students
        ])


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "areas_of_expertise": request.user.areas_of_expertise or "",
            "project_interests": request.user.project_interests or "",
        })

    def put(self, request):
        updated_fields = []
        if "areas_of_expertise" in request.data:
            value = request.data.get("areas_of_expertise") or ""
            if not isinstance(value, str) or len(value) > 500:
                return Response(
                    {"error": "areas_of_expertise must be a string up to 500 characters"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            request.user.areas_of_expertise = value
            updated_fields.append("areas_of_expertise")
        if "project_interests" in request.data:
            value = request.data.get("project_interests") or ""
            if not isinstance(value, str) or len(value) > 500:
                return Response(
                    {"error": "project_interests must be a string up to 500 characters"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            request.user.project_interests = value
            updated_fields.append("project_interests")
        if not updated_fields:
            return Response(
                {"error": "No recognised profile fields supplied"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        request.user.save(update_fields=updated_fields)
        return Response({
            "areas_of_expertise": request.user.areas_of_expertise,
            "project_interests": request.user.project_interests,
            "updated_fields": updated_fields,
        })


class BenchmarkPreferenceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'student':
            return Response(
                {"error": "Only students can manage benchmark preferences"},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response({"benchmark_opt_in": bool(request.user.benchmark_opt_in)})

    def put(self, request):
        if request.user.role != 'student':
            return Response(
                {"error": "Only students can manage benchmark preferences"},
                status=status.HTTP_403_FORBIDDEN,
            )
        opt_in = request.data.get('benchmark_opt_in')
        if not isinstance(opt_in, bool):
            return Response(
                {"error": "benchmark_opt_in must be a boolean"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        request.user.benchmark_opt_in = opt_in
        request.user.save(update_fields=["benchmark_opt_in"])
        return Response({"benchmark_opt_in": opt_in})


class CohortBenchmarkView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'student':
            return Response(
                {"error": "Only students can view their cohort benchmark"},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response(build_cohort_benchmark(request.user))


class DefenseQuestionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'student':
            return Response(
                {"error": "Only students can request defense questions"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            limit = int(request.query_params.get('limit', 5))
        except (TypeError, ValueError):
            return Response(
                {"error": "limit must be an integer"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if limit < 1 or limit > 25:
            return Response(
                {"error": "limit must be between 1 and 25"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        milestone = request.query_params.get('milestone')
        if milestone and milestone not in dict(Submission.MILESTONE_CHOICES):
            return Response(
                {"error": "milestone is not a recognized value"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        category = request.query_params.get('category')
        if category and category not in CATEGORY_LABELS:
            return Response(
                {"error": "category is not a recognized value"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        difficulty = request.query_params.get('difficulty')
        if difficulty and difficulty not in DIFFICULTY_LEVELS:
            return Response(
                {"error": "difficulty is not a recognized value"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = build_defense_seeds(
            request.user,
            milestone=milestone,
            category=category,
            difficulty=difficulty,
            limit=limit,
        )
        return Response({
            "student": {"id": request.user.id},
            "available_categories": result["available_categories"],
            "available_difficulties": result["available_difficulties"],
            "warnings": result["warnings"],
            "seeds": result["seeds"],
        })


class SuggestSupervisorView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        try:
            limit = int(request.query_params.get('limit', 5))
        except (TypeError, ValueError):
            return Response(
                {"error": "limit must be an integer"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if limit < 1 or limit > 10:
            return Response(
                {"error": "limit must be between 1 and 10"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        supervisor_id = request.query_params.get('supervisor_id')
        student_id = request.query_params.get('student_id')
        if supervisor_id and student_id:
            return Response(
                {"error": "supply either supervisor_id or student_id, not both"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if supervisor_id:
            try:
                supervisor = User.objects.get(id=supervisor_id, role="supervisor")
            except User.DoesNotExist:
                return Response(
                    {"error": "Supervisor not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            if supervisor.remaining_capacity <= 0:
                return Response(
                    {"error": "Supervisor has no remaining capacity"},
                    status=status.HTTP_409_CONFLICT,
                )
            result = suggest_students_for_supervisor(supervisor, limit=limit)
            return Response(result)

        if not student_id:
            return Response(
                {"error": "student_id or supervisor_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            student = User.objects.get(id=student_id, role="student")
        except User.DoesNotExist:
            return Response(
                {"error": "Student not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        result = suggest_supervisors(student, limit=limit)
        return Response(result)


class StalledStudentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in {'supervisor', 'admin'}:
            return Response(
                {"error": "Only supervisors and admins can view stalled students"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            threshold = int(request.query_params.get('threshold_days', 21))
        except (TypeError, ValueError):
            return Response(
                {"error": "threshold_days must be an integer"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if threshold < 1 or threshold > 90:
            return Response(
                {"error": "threshold_days must be between 1 and 90"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = list_stalled_students(request.user, threshold_days=threshold)
        return Response(result)


class SubmissionDiffView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, submission_id):
        if request.user.role != 'supervisor':
            return Response(
                {"error": "Only supervisors can view submission diffs"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            submission = Submission.objects.select_related('project', 'project__student', 'project__supervisor').get(pk=submission_id)
        except Submission.DoesNotExist:
            return Response({"error": "Submission not found"}, status=status.HTTP_404_NOT_FOUND)

        if submission.project.supervisor_id != request.user.id:
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        compare_to_id = request.query_params.get('compare_to')
        if compare_to_id:
            try:
                previous = Submission.objects.select_related('project', 'project__supervisor').get(pk=compare_to_id)
            except Submission.DoesNotExist:
                return Response({"error": "Comparison submission not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            previous = submission.previous

        if previous is None:
            return Response({
                "submission": {
                    "id": submission.id,
                    "project_id": submission.project_id,
                    "milestone": submission.milestone,
                    "version": submission.version,
                    "extraction_status": submission.extraction_status,
                },
                "comparison": None,
                "diff": None,
                "feedback_coverage": [],
                "warnings": ["This is the first version; there is no previous submission to compare against."],
            })

        if (
            previous.project_id != submission.project_id
            or previous.milestone != submission.milestone
        ):
            return Response(
                {"error": "Comparison submission must belong to the same project and milestone"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if previous.project.supervisor_id != request.user.id:
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        warnings = []
        if submission.extraction_status != 'success' or previous.extraction_status != 'success':
            warnings.append(
                "Text extraction was incomplete for one or both submissions; diff and coverage are limited."
            )

        diff = compute_diff(previous.extracted_text or '', submission.extracted_text or '')
        reviews = SubmissionReview.objects.filter(submission=previous).select_related('reviewer')
        coverage, coverage_warnings = evaluate_feedback_coverage(reviews, submission.extracted_text or '')
        warnings.extend(coverage_warnings)

        return Response({
            "submission": {
                "id": submission.id,
                "project_id": submission.project_id,
                "milestone": submission.milestone,
                "version": submission.version,
                "extraction_status": submission.extraction_status,
            },
            "comparison": {
                "id": previous.id,
                "project_id": previous.project_id,
                "milestone": previous.milestone,
                "version": previous.version,
                "extraction_status": previous.extraction_status,
            },
            "diff": diff,
            "feedback_coverage": coverage,
            "warnings": warnings,
        })


class SubmissionReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, submission_id):
        try:
            submission = Submission.objects.get(id=submission_id)
        except Submission.DoesNotExist:
            return Response(
                {"error": "Submission not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.user
        if user.role == 'supervisor':
            if submission.project.supervisor != user:
                return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        elif user.role == 'student':
            if submission.project.student != user:
                return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        elif user.role == 'admin':
            pass
        else:
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        reviews = submission.reviews.select_related('reviewer').order_by('-reviewed_at')
        return Response(SubmissionReviewSerializer(reviews, many=True).data)


import requests
import io
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