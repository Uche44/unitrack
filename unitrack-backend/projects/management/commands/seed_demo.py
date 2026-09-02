"""Idempotent demo seed for the UniTrack WebMCP walkthrough.

Seeds only Computer Science accounts using realistic Nigerian names for both
supervisors (with lecturer titles) and students, so the cohort benchmark tool
has at least five eligible students and the assignment/stalled tools have
meaningful data.
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
STALLED_DAYS = 30


SUPERVISOR_PROFILES = [
    (
        "prof-okonkwo@unitrack-demo.test",
        "Prof. Adaeze Okonkwo",
        "nlp, machine learning, recommender systems",
    ),
    (
        "dr-balogun@unitrack-demo.test",
        "Dr. Tunde Balogun",
        "computer vision, medical imaging, deep learning",
    ),
    (
        "dr-adeyemi@unitrack-demo.test",
        "Dr. Ifeoma Adeyemi",
        "robotics, embedded systems, control systems",
    ),
    (
        "dr-okafor@unitrack-demo.test",
        "Dr. Chinedu Okafor",
        "data mining, anomaly detection, big data",
    ),
    (
        "dr-ibrahim@unitrack-demo.test",
        "Dr. Halima Ibrahim",
        "cybersecurity, cryptography, network security",
    ),
]


ACTIVE_STUDENTS = [
    ("ada.okafor@students.unitrack-demo.test", "Adaeze Okafor", "nlp, recommendation systems"),
    ("tunde.balogun@students.unitrack-demo.test", "Tunde Balogun", "computer vision, medical imaging"),
    ("ife.adeyemi@students.unitrack-demo.test", "Ifeoma Adeyemi", "robotics, embedded systems"),
    ("chinedu.eze@students.unitrack-demo.test", "Chinedu Eze", "data mining, anomaly detection"),
    ("halima.sani@students.unitrack-demo.test", "Halima Sani", "cybersecurity, cryptography"),
    ("oluwaseun.adebayo@students.unitrack-demo.test", "Oluwaseun Adebayo", "machine learning, deep learning"),
    ("chisom.okeke@students.unitrack-demo.test", "Chisom Okeke", "nlp, sentiment analysis"),
    ("amaka.nwosu@students.unitrack-demo.test", "Amaka Nwosu", "computer vision, robotics"),
]


STALLED_STUDENTS = [
    ("emeka.obi@students.unitrack-demo.test", "Emeka Obi", "robotics, embedded systems"),
    ("yinka.adeola@students.unitrack-demo.test", "Yinka Adeola", "cybersecurity, network security"),
]


UNASSIGNED_STUDENTS = [
    ("bisi.akinwale@students.unitrack-demo.test", "Bisi Akinwale", "nlp, machine translation"),
    ("damola.folarin@students.unitrack-demo.test", "Damola Folarin", "robotics, drone navigation"),
    ("funke.adebisi@students.unitrack-demo.test", "Funke Adebisi", "data mining, healthcare analytics"),
]


class Command(BaseCommand):
    help = "Seed the Computer Science demo dataset (3 login accounts + rich relations)."

    def add_arguments(self, parser):
        parser.add_argument("--password", default=PASSWORD)
        parser.add_argument("--stalled-days", type=int, default=STALLED_DAYS)

    def handle(self, *args, **options):
        password = options["password"]
        stalled_days = options["stalled_days"]
        with transaction.atomic():
            session = self._ensure_session()
            tags = self._ensure_tags()
            admin = self._ensure_admin(password)
            supervisors = self._ensure_supervisors(password, tags)
            lead_supervisor = supervisors[0]
            student = self._ensure_student(password, lead_supervisor, session)
            self._ensure_chapters(student, lead_supervisor)
            self._ensure_active_students(supervisors, session)
            self._ensure_stalled_students(supervisors, session, stalled_days)
            self._ensure_unassigned_students(session)

        self.stdout.write(self.style.SUCCESS("Demo dataset ready."))
        self.stdout.write(f"  admin     : {admin.email} / {password}")
        self.stdout.write(f"  supervisor: {lead_supervisor.email} / {password}")
        self.stdout.write(f"  student   : {student.email} / {password}")

    def _ensure_session(self):
        session, _ = ProjectSession.objects.get_or_create(
            session="2026/2027",
            defaults={
                "duration": "12 months",
                "start_date": timezone.localdate() - timedelta(days=30),
                "end_date": timezone.localdate() + timedelta(days=300),
                "is_active": True,
            },
        )
        return session

    def _ensure_tags(self):
        names = ["nlp", "computer vision", "robotics", "data mining", "cybersecurity"]
        return {name: Tag.objects.get_or_create(name=name)[0] for name in names}

    def _ensure_admin(self, password):
        admin, created = User.objects.get_or_create(
            email="hod.cs@unitrack-demo.test",
            defaults={
                "full_name": "Dr. Ngozi Eze",
                "role": "admin",
                "department": DEPARTMENT,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if not created:
            admin.full_name = "Dr. Ngozi Eze"
            admin.department = DEPARTMENT
            admin.is_staff = True
            admin.is_superuser = True
            admin.set_password(password)
            admin.save()
        else:
            admin.set_password(password)
            admin.save()
        return admin

    def _ensure_supervisors(self, password, tags):
        supervisors = []
        for email, name, expertise in SUPERVISOR_PROFILES:
            supervisor, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "full_name": name,
                    "role": "supervisor",
                    "department": DEPARTMENT,
                    "is_approved": True,
                    "capacity": 5,
                    "areas_of_expertise": expertise,
                },
            )
            if created:
                supervisor.set_password(password)
                supervisor.save()
            supervisors.append(supervisor)
        supervisors[0].expertise_tags.set([tags["nlp"]])
        return supervisors

    def _ensure_student(self, password, supervisor, session):
        student, created = User.objects.get_or_create(
            email="student-demo@students.unitrack-demo.test",
            defaults={
                "full_name": "Emeka Onyebuchi",
                "role": "student",
                "department": DEPARTMENT,
                "matric_no": "CSC/2023/099",
                "is_approved": True,
                "is_assigned": True,
                "supervisor": supervisor,
                "project_interests": "nlp, recommendation systems",
            },
        )
        if created:
            student.set_password(password)
            student.save()
            Project.objects.get_or_create(
                student=student,
                supervisor=supervisor,
                session=session,
                defaults={
                    "title": "NLP-Based Course Recommender",
                    "description": "Walkthrough project for the WebMCP demo.",
                    "status": "in_progress",
                    "is_approved": True,
                },
            )
        return student

    def _ensure_chapters(self, student, supervisor):
        project = student.projects.first()
        if not project:
            return
        Submission.objects.get_or_create(
            project=project,
            milestone="chapter_one",
            version=1,
            defaults={
                "file_url": "https://example.com/chapter-one-v1.pdf",
                "extracted_text": (
                    "Chapter One: Introduction\n"
                    "The objective is to evaluate citation issues in prior work.\n"
                    "We used a mixed method approach with quantitative results.\n"
                    "Natural Language Processing drives the analysis."
                ),
                "extraction_status": "success",
                "is_approved": False,
                "is_rejected": True,
                "rejection_comment": (
                    "Citation needs improvement and methodology is unclear."
                ),
            },
        )
        SubmissionReview.objects.get_or_create(
            submission=project.submissions.first(),
            reviewer=supervisor,
            decision="rejected",
            feedback=(
                "Citation needs improvement and methodology is unclear. "
                "Please revise the methodology section and update references."
            ),
        )
        Submission.objects.get_or_create(
            project=project,
            milestone="chapter_one",
            version=2,
            defaults={
                "file_url": "https://example.com/chapter-one-v2.pdf",
                "extracted_text": (
                    "Chapter One: Introduction\n"
                    "The objective is to evaluate citation issues in prior work.\n"
                    "We used a mixed method approach with quantitative results.\n"
                    "Natural Language Processing drives the analysis.\n"
                    "We expanded the methodology section with sampling and data sources."
                ),
                "extraction_status": "success",
                "is_approved": True,
                "is_rejected": False,
            },
        )

    def _ensure_active_students(self, supervisors, session):
        states = ["in_progress"] * 6 + ["proposal_approved"] * 2
        for index, (email, name, interests) in enumerate(ACTIVE_STUDENTS):
            supervisor = supervisors[index % len(supervisors)]
            matric = f"CSC/2023/{index + 100:03d}"
            student, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "full_name": name,
                    "role": "student",
                    "department": DEPARTMENT,
                    "matric_no": matric,
                    "is_approved": True,
                    "is_assigned": True,
                    "supervisor": supervisor,
                    "project_interests": interests,
                },
            )
            if created:
                student.set_password(PASSWORD)
                student.save()
            Project.objects.get_or_create(
                student=student,
                supervisor=supervisor,
                session=session,
                defaults={
                    "title": f"{name.split()[-1]}'s Final Year Project",
                    "status": states[index % len(states)],
                    "is_approved": True,
                },
            )

    def _ensure_stalled_students(self, supervisors, session, stalled_days):
        stalled_at = timezone.now() - timedelta(days=stalled_days)
        for index, (email, name, interests) in enumerate(STALLED_STUDENTS):
            # Always assign stalled students to the demo lead supervisor
            # so they appear in the demo account's stalled list.
            supervisor = supervisors[0]
            student, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "full_name": name,
                    "role": "student",
                    "department": DEPARTMENT,
                    "matric_no": f"CSC/2023/{200 + index:03d}",
                    "is_approved": True,
                    "is_assigned": True,
                    "supervisor": supervisor,
                    "project_interests": interests,
                },
            )
            if created:
                student.set_password(PASSWORD)
                student.save()
            project, _ = Project.objects.get_or_create(
                student=student,
                supervisor=supervisor,
                session=session,
                defaults={
                    "title": f"{name.split()[-1]}'s Stalled Project",
                    "status": "in_progress",
                    "is_approved": True,
                },
            )
            # Override auto_now_add so both the project and submission are backdated.
            Project.objects.filter(pk=project.pk).update(created_at=stalled_at)
            Submission.objects.get_or_create(
                project=project,
                milestone="proposal",
                version=1,
                defaults={
                    "file_url": "https://example.com/stalled.pdf",
                    "extracted_text": "Proposal draft.",
                    "extraction_status": "success",
                },
            )
            # Override auto_now_add so the submission is backdated for demo purposes.
            Submission.objects.filter(
                project=project, milestone="proposal", version=1
            ).update(submitted_at=stalled_at)
            SupervisorContact.objects.get_or_create(
                student=student,
                supervisor=supervisor,
                session=session,
                defaults={
                    "contact_type": "message",
                    "note": "Last contact was several weeks ago.",
                    "occurred_at": stalled_at,
                },
            )

    def _ensure_unassigned_students(self, session):
        for index, (email, name, interests) in enumerate(UNASSIGNED_STUDENTS):
            matric = f"CSC/2023/{300 + index:03d}"
            student, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "full_name": name,
                    "role": "student",
                    "department": DEPARTMENT,
                    "matric_no": matric,
                    "is_approved": True,
                    "is_assigned": False,
                    "project_interests": interests,
                },
            )
            if created:
                student.set_password(PASSWORD)
                student.save()
            Project.objects.get_or_create(
                student=student,
                supervisor=None,
                session=session,
                defaults={
                    "title": f"{name.split()[-1]}'s Hypothetical Project",
                    "status": "proposal_pending",
                    "is_approved": False,
                },
            )