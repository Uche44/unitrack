"""Idempotent demo seed for the UniTrack WebMCP walkthrough.

Seeds the hackathon judge accounts:
- Supervisor: dr.chukwu@example.com (assigned to 5 students)
- Student: obi@example.com (Obi Arinze) - up to Chapter 2 with 2 versions

Includes additional students with varying progress, feedback themes, and
unassigned students for testing the suggest supervisor tool.
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import Tag, User
from projects.models import (
    Project,
    ProjectSession,
    Submission,
    SubmissionReview,
    SupervisorContact,
)


DEPARTMENT = "Computer Science"
PASSWORD = "demo-pass-123"
STALLED_DAYS = 35

# Judge accounts
JUDGE_SUPERVISOR = {
    "email": "dr.chukwu@example.com",
    "password": "c1234567",
    "full_name": "Dr. Chukwu Okonkwo",
    "expertise": "machine learning, nlp, data mining, recommendation systems",
}

JUDGE_STUDENT = {
    "email": "obi@example.com",
    "password": "o12qwera",
    "full_name": "Obi Arinze",
    "matric_no": "2022/001",
    "interests": "machine learning, recommendation systems",
}

# Additional students under Dr. Chukwu (5 total including Obi)
ADDITIONAL_STUDENTS = [
    {
        "email": "adaeze.nwosu@example.com",
        "full_name": "Adaeze Nwosu",
        "matric_no": "2022/002",
        "interests": "nlp, sentiment analysis",
        "progress": "proposal_pending",
    },
    {
        "email": "chidi.eze@example.com",
        "full_name": "Chidi Eze",
        "matric_no": "2022/003",
        "interests": "machine learning, computer vision",
        "progress": "chapter_one_approved",
    },
    {
        "email": "nneka.okeke@example.com",
        "full_name": "Nneka Okeke",
        "matric_no": "2022/004",
        "interests": "data mining, analytics",
        "progress": "chapter_one_pending",
    },
    {
        "email": "emeka.obi@example.com",
        "full_name": "Emeka Obi",
        "matric_no": "2022/005",
        "interests": "recommendation systems",
        "progress": "stalled",
    },
]

# Unassigned students for suggest supervisor tool testing
UNASSIGNED_STUDENTS = [
    {
        "email": "tosin.adebayo@example.com",
        "full_name": "Tosin Adebayo",
        "matric_no": "2022/201",
        "interests": "cybersecurity, network security",
    },
    {
        "email": "uche.nwankwo@example.com",
        "full_name": "Uche Nwankwo",
        "matric_no": "2022/202",
        "interests": "artificial intelligence, expert systems",
    },
    {
        "email": "kemi.ogunleye@example.com",
        "full_name": "Kemi Ogunleye",
        "matric_no": "2022/203",
        "interests": "cloud computing, distributed systems",
    },
]

# Feedback themes for testing
FEEDBACK_THEMES = {
    "literature_review": (
        "The literature review needs more depth. "
        "Please include more recent publications (2020-2024) and "
        "provide better synthesis of existing work rather than just listing sources."
    ),
    "citation_formatting": (
        "Citation formatting needs improvement. "
        "Ensure all references follow APA 7th edition format consistently. "
        "Check in-text citations match the reference list."
    ),
}


class Command(BaseCommand):
    help = "Seed the hackathon demo dataset with judge accounts."

    def add_arguments(self, parser):
        parser.add_argument("--password", default=PASSWORD)
        parser.add_argument("--stalled-days", type=int, default=STALLED_DAYS)
        parser.add_argument("--flush", action="store_true", help="Clear old demo data before seeding")

    def handle(self, *args, **options):
        password = options["password"]
        stalled_days = options["stalled_days"]
        
        with transaction.atomic():
            if options["flush"]:
                self._flush_old_demo_data()
            session = self._ensure_session()
            tags = self._ensure_tags()
            admin = self._ensure_admin(password)
            supervisor = self._ensure_supervisor(password, tags)
            judge_student = self._ensure_judge_student(password, supervisor, session)
            self._ensure_judge_student_chapters(judge_student, supervisor)
            self._ensure_additional_students(password, supervisor, session, stalled_days)
            self._ensure_unassigned_students(session)

        self.stdout.write(self.style.SUCCESS("Demo dataset ready."))
        self.stdout.write(f"  Admin     : {admin.email} / {password}")
        self.stdout.write(f"  Supervisor: {supervisor.email} / {JUDGE_SUPERVISOR['password']}")
        self.stdout.write(f"  Student   : {judge_student.email} / {JUDGE_STUDENT['password']}")

    def _flush_old_demo_data(self):
        """Clear old demo data from previous seed scripts."""
        self.stdout.write("Flushing old demo data...")
        
        # Delete old demo users (by email patterns)
        old_patterns = [
            "@students.unitrack-demo.test",
            "@unitrack-demo.test",
        ]
        for pattern in old_patterns:
            User.objects.filter(email__icontains=pattern).delete()
        
        # Delete old sessions
        ProjectSession.objects.filter(session="2026/2027").delete()
        
        self.stdout.write(self.style.SUCCESS("Old demo data flushed."))

    def _ensure_session(self):
        """Create 2025/2026 academic session."""
        session, _ = ProjectSession.objects.get_or_create(
            session="2025/2026",
            defaults={
                "duration": "12 months",
                "start_date": timezone.localdate() - timedelta(days=60),
                "end_date": timezone.localdate() + timedelta(days=300),
                "is_active": True,
            },
        )
        return session

    def _ensure_tags(self):
        """Create expertise/topic tags."""
        names = ["nlp", "machine learning", "data mining", "recommendation systems", 
                 "computer vision", "deep learning"]
        return {name: Tag.objects.get_or_create(name=name)[0] for name in names}

    def _ensure_admin(self, password):
        """Create admin user."""
        admin, created = User.objects.get_or_create(
            email="admin@unitrack.test",
            defaults={
                "full_name": "Admin User",
                "role": "admin",
                "department": DEPARTMENT,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin.set_password(password)
        admin.save()
        return admin

    def _ensure_supervisor(self, password, tags):
        """Create Dr. Chukwu - the judge supervisor account."""
        supervisor, created = User.objects.get_or_create(
            email=JUDGE_SUPERVISOR["email"],
            defaults={
                "full_name": JUDGE_SUPERVISOR["full_name"],
                "role": "supervisor",
                "department": DEPARTMENT,
                "is_approved": True,
                "capacity": 10,
                "areas_of_expertise": JUDGE_SUPERVISOR["expertise"],
                "staff_id": "CS/001",
            },
        )
        supervisor.set_password(JUDGE_SUPERVISOR["password"])
        supervisor.is_approved = True
        supervisor.save()
        # Set expertise tags
        supervisor.expertise_tags.set([
            tags["machine learning"],
            tags["nlp"],
            tags["data mining"],
            tags["recommendation systems"],
        ])
        return supervisor

    def _ensure_judge_student(self, password, supervisor, session):
        """Create Obi Arinze - the judge student account."""
        student, created = User.objects.get_or_create(
            email=JUDGE_STUDENT["email"],
            defaults={
                "full_name": JUDGE_STUDENT["full_name"],
                "role": "student",
                "department": DEPARTMENT,
                "matric_no": JUDGE_STUDENT["matric_no"],
                "is_approved": True,
                "is_assigned": True,
                "supervisor": supervisor,
                "project_interests": JUDGE_STUDENT["interests"],
            },
        )
        student.set_password(JUDGE_STUDENT["password"])
        student.is_approved = True
        student.is_assigned = True
        student.supervisor = supervisor
        student.save()
        
        # Create project
        Project.objects.get_or_create(
            student=student,
            defaults={
                "supervisor": supervisor,
                "session": session,
                "title": "Machine Learning-Based Course Recommendation System",
                "description": "A recommendation system for course selection using collaborative filtering and NLP.",
                "status": "in_progress",
                "is_approved": True,
            },
        )
        return student

    def _ensure_judge_student_chapters(self, student, supervisor):
        """Create Chapter 1 (approved) and Chapter 2 (v1 rejected, v2 pending review)."""
        project = student.projects.first()
        if not project:
            return

        # Chapter 1 - Approved
        chapter_one, _ = Submission.objects.get_or_create(
            project=project,
            milestone="chapter_one",
            version=1,
            defaults={
                "file_url": "https://example.com/obi-chapter1-v1.pdf",
                "extracted_text": (
                    "Chapter One: Introduction\n"
                    "This project proposes a machine learning-based course recommendation system.\n"
                    "The system will use collaborative filtering and content-based approaches.\n"
                    "Natural Language Processing will analyze student preferences."
                ),
                "extraction_status": "success",
                "is_approved": True,
                "is_rejected": False,
            },
        )
        SubmissionReview.objects.get_or_create(
            submission=chapter_one,
            reviewer=supervisor,
            defaults={
                "decision": "approved",
                "feedback": "Good introduction. Proceed to Chapter 2.",
            },
        )

        # Chapter 2 - Version 1 (Rejected with feedback themes)
        chapter_two_v1, _ = Submission.objects.get_or_create(
            project=project,
            milestone="chapter_two",
            version=1,
            defaults={
                "file_url": "https://example.com/obi-chapter2-v1.pdf",
                "extracted_text": (
                    "Chapter Two: Literature Review\n"
                    "This chapter reviews existing work on recommendation systems.\n"
                    "Collaborative filtering was discussed by Smith (2019).\n"
                    "Content-based approaches were explored by Jones (2018).\n"
                    "Deep learning methods have shown promise."
                ),
                "extraction_status": "success",
                "is_approved": False,
                "is_rejected": True,
                "rejection_comment": (
                    f"{FEEDBACK_THEMES['literature_review']} "
                    f"{FEEDBACK_THEMES['citation_formatting']}"
                ),
            },
        )
        SubmissionReview.objects.get_or_create(
            submission=chapter_two_v1,
            reviewer=supervisor,
            defaults={
                "decision": "rejected",
                "feedback": (
                    f"{FEEDBACK_THEMES['literature_review']} "
                    f"{FEEDBACK_THEMES['citation_formatting']}"
                ),
            },
        )

        # Chapter 2 - Version 2 (Revised, pending review)
        chapter_two_v2, _ = Submission.objects.get_or_create(
            project=project,
            milestone="chapter_two",
            version=2,
            defaults={
                "file_url": "https://example.com/obi-chapter2-v2.pdf",
                "extracted_text": (
                    "Chapter Two: Literature Review\n"
                    "This chapter provides a comprehensive review of recommendation systems.\n\n"
                    "2.1 Collaborative Filtering\n"
                    "Smith, J. & Brown, A. (2022) demonstrated that collaborative filtering "
                    "achieves 85% accuracy in course recommendations. Their work at MIT "
                    "showed significant improvements over earlier methods (Smith, 2019).\n\n"
                    "2.2 Content-Based Approaches\n"
                    "Jones, M. et al. (2023) explored content-based filtering with "
                    "NLP features. Recent work by Lee (2024) combined this with "
                    "deep learning for better personalization.\n\n"
                    "2.3 Deep Learning Methods\n"
                    "Recent advances in transformer models (Vaswani et al., 2023) "
                    "have enabled more accurate recommendations. Wang (2024) achieved "
                    "state-of-the-art results using BERT-based approaches.\n\n"
                    "References\n"
                    "Jones, M., Kim, S., & Patel, R. (2023). Content-based recommendation "
                    "with NLP. Journal of ML Research, 24(3), 112-128.\n"
                    "Lee, H. (2024). Deep learning for personalization. AI Conference Proceedings.\n"
                    "Smith, J. & Brown, A. (2022). Collaborative filtering in education. "
                    "Educational Technology Journal, 15(2), 45-62.\n"
                    "Vaswani, A. et al. (2023). Attention mechanisms in recommendation. "
                    "Nature Machine Intelligence, 5, 234-251.\n"
                    "Wang, X. (2024). BERT-based recommendation systems. arXiv:2024.12345."
                ),
                "extraction_status": "success",
                "is_approved": False,
                "is_rejected": False,
                "previous": chapter_two_v1,
            },
        )

    def _ensure_additional_students(self, password, supervisor, session, stalled_days):
        """Create 4 additional students under Dr. Chukwu with varying progress."""
        stalled_at = timezone.now() - timedelta(days=stalled_days)
        
        for student_data in ADDITIONAL_STUDENTS:
            student, created = User.objects.get_or_create(
                email=student_data["email"],
                defaults={
                    "full_name": student_data["full_name"],
                    "role": "student",
                    "department": DEPARTMENT,
                    "matric_no": student_data["matric_no"],
                    "is_approved": True,
                    "is_assigned": True,
                    "supervisor": supervisor,
                    "project_interests": student_data["interests"],
                },
            )
            if created:
                student.set_password(password)
                student.save()

            # Create project based on progress
            progress = student_data["progress"]
            project_status = "in_progress" if progress != "proposal_pending" else "proposal_pending"
            
            project, _ = Project.objects.get_or_create(
                student=student,
                defaults={
                    "supervisor": supervisor,
                    "session": session,
                    "title": f"{student_data['full_name'].split()[-1]}'s Final Year Project",
                    "status": project_status,
                    "is_approved": True,
                },
            )

            # Add submissions and feedback based on progress
            if progress == "proposal_pending":
                # Just proposal submitted
                Submission.objects.get_or_create(
                    project=project,
                    milestone="proposal",
                    version=1,
                    defaults={
                        "file_url": f"https://example.com/{student_data['matric_no']}-proposal.pdf",
                        "extracted_text": "Project proposal draft.",
                        "extraction_status": "success",
                        "is_approved": False,
                        "is_rejected": False,
                    },
                )
            
            elif progress == "chapter_one_pending":
                # Proposal approved, Chapter 1 pending review
                Submission.objects.get_or_create(
                    project=project,
                    milestone="proposal",
                    version=1,
                    defaults={
                        "file_url": f"https://example.com/{student_data['matric_no']}-proposal.pdf",
                        "extracted_text": "Project proposal.",
                        "extraction_status": "success",
                        "is_approved": True,
                    },
                )
                sub, _ = Submission.objects.get_or_create(
                    project=project,
                    milestone="chapter_one",
                    version=1,
                    defaults={
                        "file_url": f"https://example.com/{student_data['matric_no']}-chapter1.pdf",
                        "extracted_text": "Chapter one draft with some citations.",
                        "extraction_status": "success",
                        "is_approved": False,
                        "is_rejected": False,
                    },
                )
            
            elif progress == "chapter_one_approved":
                # Chapter 1 approved with feedback
                Submission.objects.get_or_create(
                    project=project,
                    milestone="proposal",
                    version=1,
                    defaults={
                        "file_url": f"https://example.com/{student_data['matric_no']}-proposal.pdf",
                        "extracted_text": "Project proposal.",
                        "extraction_status": "success",
                        "is_approved": True,
                    },
                )
                sub, _ = Submission.objects.get_or_create(
                    project=project,
                    milestone="chapter_one",
                    version=1,
                    defaults={
                        "file_url": f"https://example.com/{student_data['matric_no']}-chapter1.pdf",
                        "extracted_text": "Chapter one with literature review.",
                        "extraction_status": "success",
                        "is_approved": True,
                    },
                )
                SubmissionReview.objects.get_or_create(
                    submission=sub,
                    reviewer=supervisor,
                    defaults={
                        "decision": "approved",
                        "feedback": FEEDBACK_THEMES["literature_review"],
                    },
                )
            
            elif progress == "stalled":
                # Stalled student - backdate everything
                Project.objects.filter(pk=project.pk).update(created_at=stalled_at)
                
                Submission.objects.get_or_create(
                    project=project,
                    milestone="proposal",
                    version=1,
                    defaults={
                        "file_url": f"https://example.com/{student_data['matric_no']}-proposal.pdf",
                        "extracted_text": "Initial proposal draft.",
                        "extraction_status": "success",
                        "is_approved": True,
                    },
                )
                Submission.objects.filter(
                    project=project, milestone="proposal", version=1
                ).update(submitted_at=stalled_at)
                
                # Add rejected chapter one with feedback themes
                sub, _ = Submission.objects.get_or_create(
                    project=project,
                    milestone="chapter_one",
                    version=1,
                    defaults={
                        "file_url": f"https://example.com/{student_data['matric_no']}-chapter1.pdf",
                        "extracted_text": "Chapter one draft.",
                        "extraction_status": "success",
                        "is_approved": False,
                        "is_rejected": True,
                        "rejection_comment": f"{FEEDBACK_THEMES['literature_review']} {FEEDBACK_THEMES['citation_formatting']}",
                    },
                )
                Submission.objects.filter(
                    project=project, milestone="chapter_one", version=1
                ).update(submitted_at=stalled_at)
                
                SubmissionReview.objects.get_or_create(
                    submission=sub,
                    reviewer=supervisor,
                    defaults={
                        "decision": "rejected",
                        "feedback": f"{FEEDBACK_THEMES['literature_review']} {FEEDBACK_THEMES['citation_formatting']}",
                    },
                )
                
                # Log old contact
                SupervisorContact.objects.get_or_create(
                    student=student,
                    supervisor=supervisor,
                    session=session,
                    defaults={
                        "contact_type": "email",
                        "note": "Followed up on stalled progress. No response.",
                        "occurred_at": stalled_at,
                    },
                )

    def _ensure_unassigned_students(self, session):
        """Create unassigned students for suggest supervisor tool testing."""
        for student_data in UNASSIGNED_STUDENTS:
            student, created = User.objects.get_or_create(
                email=student_data["email"],
                defaults={
                    "full_name": student_data["full_name"],
                    "role": "student",
                    "department": DEPARTMENT,
                    "matric_no": student_data["matric_no"],
                    "is_approved": True,
                    "is_assigned": False,
                    "project_interests": student_data["interests"],
                },
            )
            if created:
                student.set_password(PASSWORD)
                student.save()
            
            # Create project without supervisor
            Project.objects.get_or_create(
                student=student,
                defaults={
                    "supervisor": None,
                    "session": session,
                    "title": f"{student_data['full_name'].split()[-1]}'s Proposed Project",
                    "status": "proposal_pending",
                    "is_approved": False,
                },
            )
