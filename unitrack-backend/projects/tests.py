from unittest.mock import patch
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.factories import create_admin, create_student, create_supervisor
from projects.factories import (
    create_contact,
    create_project,
    create_review,
    create_session,
    create_submission,
)
from projects.models import Project, Submission, SubmissionReview
from projects.utils import pdf_text


class SessionPermissionTests(APITestCase):
    def setUp(self):
        self.admin = create_admin()
        self.student = create_student()

    def test_only_admin_can_create_session(self):
        payload = {
            "session": "2026/2027",
            "duration": "12 months",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
        }

        self.client.force_authenticate(self.student)
        response = self.client.post(
            reverse("project-session"), payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.admin)
        response = self.client.post(
            reverse("project-session"), payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_anonymous_cannot_read_sessions(self):
        response = self.client.get(reverse("project-session"))
        # DRF returns 401 for unauthenticated requests when the view requires
        # IsAuthenticated. Accept both codes; the requirement is that the read
        # is not public.
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_authenticated_user_can_read_sessions(self):
        create_session()
        self.client.force_authenticate(self.student)
        response = self.client.get(reverse("project-session"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CreateSubmissionOwnershipTests(APITestCase):
    def setUp(self):
        self.admin = create_admin()
        supervisor = create_supervisor()
        self.student_a = create_student(supervisor=supervisor)
        self.student_b = create_student(supervisor=supervisor)
        self.project_a = create_project(
            student=self.student_a, supervisor=supervisor
        )

    def test_student_cannot_submit_to_another_students_project(self):
        self.client.force_authenticate(self.student_b)
        response = self.client.post(
            reverse("create-submission"),
            {"project": self.project_a.id, "milestone": "proposal"},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_student_cannot_submit(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            reverse("create-submission"),
            {"project": self.project_a.id, "milestone": "proposal"},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_submits_to_own_project(self):
        self.client.force_authenticate(self.student_a)
        pdf = SimpleUploadedFile(
            "proposal.pdf",
            b"%PDF-1.4 mock content",
            content_type="application/pdf",
        )
        payload = {
            "project": self.project_a.id,
            "milestone": "proposal",
            "file": pdf,
        }
        with patch(
            "projects.views.upload_file_to_cloudinary",
            return_value="https://cdn.example.com/proposal.pdf",
        ):
            response = self.client.post(
                reverse("create-submission"), payload, format="multipart"
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class SessionActiveStateTests(APITestCase):
    def test_only_one_active_session_at_a_time(self):
        first = create_session(is_active=True)
        second = create_session(is_active=True)

        first.refresh_from_db()
        second.refresh_from_db()

        self.assertFalse(first.is_active)
        self.assertTrue(second.is_active)

    def test_reactivating_same_session_keeps_it_active(self):
        session = create_session(is_active=True)
        session.is_active = True
        session.save()
        session.refresh_from_db()
        self.assertTrue(session.is_active)


class SupervisorCapacityTests(APITestCase):
    def test_default_capacity_is_five(self):
        supervisor = create_supervisor()
        self.assertEqual(supervisor.capacity, 5)

    def test_remaining_capacity_never_negative(self):
        supervisor = create_supervisor(capacity=0)
        self.assertEqual(supervisor.remaining_capacity, 0)

    def test_capacity_drives_approved_supervisor_listing(self):
        from rest_framework.test import APIClient

        full = create_supervisor(capacity=1)
        create_student(supervisor=full)
        open_sup = create_supervisor()

        client = APIClient()
        response = client.get("/api/supervisors/")
        ids = [s["id"] for s in response.data]
        self.assertNotIn(full.id, ids)
        self.assertIn(open_sup.id, ids)


class ContactLoggingTests(APITestCase):
    def setUp(self):
        self.supervisor = create_supervisor()
        self.other_supervisor = create_supervisor()
        self.student = create_student(supervisor=self.supervisor)
        self.outsider = create_student(supervisor=self.other_supervisor)

    def test_supervisor_can_log_contact_for_own_student(self):
        self.client.force_authenticate(self.supervisor)
        response = self.client.post(
            reverse("supervisor-contact"),
            {
                "student_id": self.student.id,
                "contact_type": "meeting",
                "note": "Discussed methodology",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_contact_rejects_mismatched_supervisor_student_pair(self):
        self.client.force_authenticate(self.supervisor)
        response = self.client.post(
            reverse("supervisor-contact"),
            {
                "student_id": self.outsider.id,
                "contact_type": "meeting",
                "note": "should not be allowed",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_supervisor_cannot_log_contact(self):
        self.client.force_authenticate(self.student)
        response = self.client.post(
            reverse("supervisor-contact"),
            {"student_id": self.student.id, "contact_type": "message"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervisor_sees_only_own_contacts(self):
        create_contact(student=self.student, supervisor=self.supervisor)
        create_contact(student=self.outsider, supervisor=self.other_supervisor)
        self.client.force_authenticate(self.supervisor)
        response = self.client.get(reverse("supervisor-contact"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class ReviewImmutabilityTests(APITestCase):
    def setUp(self):
        self.supervisor = create_supervisor()
        self.student = create_student(supervisor=self.supervisor)
        self.project = create_project(student=self.student, supervisor=self.supervisor)
        self.submission = create_submission(project=self.project)

    def test_review_cannot_be_modified(self):
        review = create_review(
            submission=self.submission, reviewer=self.supervisor, feedback="first"
        )
        review.feedback = "tampered"
        with self.assertRaises(ValidationError):
            review.save()

    def test_approve_creates_review_event(self):
        self.client.force_authenticate(self.supervisor)
        response = self.client.post(
            reverse("submission-action", kwargs={"submission_id": self.submission.id}),
            {"action": "approve"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            SubmissionReview.objects.filter(
                submission=self.submission, decision="approved"
            ).count(),
            1,
        )

    def test_reject_creates_review_event_with_feedback(self):
        self.client.force_authenticate(self.supervisor)
        response = self.client.post(
            reverse("submission-action", kwargs={"submission_id": self.submission.id}),
            {"action": "reject", "comment": "citation issues"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        review = SubmissionReview.objects.get(submission=self.submission)
        self.assertEqual(review.decision, "rejected")
        self.assertEqual(review.feedback, "citation issues")

    def test_review_endpoint_scoped_to_assigned_supervisor(self):
        create_review(
            submission=self.submission, reviewer=self.supervisor, feedback="ok"
        )
        other = create_supervisor()
        self.client.force_authenticate(other)
        response = self.client.get(
            reverse("submission-reviews", kwargs={"submission_id": self.submission.id})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.supervisor)
        response = self.client.get(
            reverse("submission-reviews", kwargs={"submission_id": self.submission.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class FeedbackThemeAnalysisTests(APITestCase):
    def setUp(self):
        self.supervisor = create_supervisor()
        self.other_supervisor = create_supervisor()
        self.session = create_session(is_active=True)
        self.other_session = create_session(is_active=False)
        self.student = create_student(supervisor=self.supervisor)
        self.project = create_project(
            student=self.student, supervisor=self.supervisor, session=self.session
        )
        self.submission = create_submission(project=self.project, milestone="proposal")
        self.other_student = create_student(supervisor=self.other_supervisor)
        self.other_project = create_project(
            student=self.other_student,
            supervisor=self.other_supervisor,
            session=self.session,
        )
        self.other_submission = create_submission(
            project=self.other_project, milestone="proposal"
        )

    def test_counts_each_review_once_per_theme_and_filters_own_scope(self):
        create_review(
            submission=self.submission,
            reviewer=self.supervisor,
            feedback="Improve the citation style and references.",
        )
        create_review(
            submission=self.submission,
            reviewer=self.supervisor,
            feedback="Citation and methodology need work.",
        )
        create_review(
            submission=self.other_submission,
            reviewer=self.other_supervisor,
            feedback="Citation issues from another supervisor.",
        )

        self.client.force_authenticate(self.supervisor)
        response = self.client.get(
            reverse("feedback-themes"),
            {"min_occurrences": 2, "limit": 7},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        themes = {item["theme"]: item for item in response.data["themes"]}
        self.assertEqual(themes["citation_formatting"]["matched_review_count"], 2)
        self.assertNotIn("methodology", themes)
        self.assertEqual(len(response.data["themes"]), 1)
        self.assertEqual(
            themes["citation_formatting"]["distinct_student_count"], 1
        )
        self.assertNotIn("student_name", response.data["themes"][0])

    def test_blank_feedback_is_excluded_and_session_is_scoped(self):
        create_review(submission=self.submission, reviewer=self.supervisor, feedback="   ")
        create_review(
            submission=self.submission,
            reviewer=self.supervisor,
            feedback="Please improve the literature review and grammar.",
        )
        old_project = create_project(
            student=self.student, supervisor=self.supervisor, session=self.other_session
        )
        old_submission = create_submission(project=old_project, milestone="proposal")
        create_review(
            submission=old_submission,
            reviewer=self.supervisor,
            feedback="The methodology and citation need revision.",
        )

        self.client.force_authenticate(self.supervisor)
        response = self.client.get(reverse("feedback-themes"), {"min_occurrences": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_reviews"], 2)
        self.assertEqual(response.data["session"], self.session.id)
        themes = {item["theme"] for item in response.data["themes"]}
        self.assertIn("literature_review", themes)
        self.assertNotIn("methodology", themes)

    def test_only_supervisor_can_read_endpoint(self):
        self.client.force_authenticate(self.other_student)
        response = self.client.get(reverse("feedback-themes"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.logout()
        response = self.client.get(reverse("feedback-themes"))
        self.assertIn(response.status_code, (401, 403))

    def test_rejects_invalid_bounds(self):
        self.client.force_authenticate(self.supervisor)
        response = self.client.get(reverse("feedback-themes"), {"limit": 8})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.get(reverse("feedback-themes"), {"min_occurrences": 0})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProfileFieldsTests(APITestCase):
    def setUp(self):
        self.admin = create_admin()
        self.supervisor = create_supervisor()
        self.student = create_student(supervisor=self.supervisor)

    def test_profile_update_validates_string(self):
        self.client.force_authenticate(self.supervisor)
        response = self.client.put(
            reverse("profile"),
            {"areas_of_expertise": "nlp, computer vision"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.supervisor.refresh_from_db()
        self.assertEqual(self.supervisor.areas_of_expertise, "nlp, computer vision")

    def test_supervisor_workload_includes_expertise(self):
        self.supervisor.areas_of_expertise = "nlp, computer vision"
        self.supervisor.save()
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse("supervisor-workload"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = next(
            row for row in response.data if row["supervisor_id"] == self.supervisor.id
        )
        self.assertEqual(item["areas_of_expertise"], "nlp, computer vision")
        self.assertIn("nlp", item["expertise_keywords"])

    def test_student_interests_returns_unassigned(self):
        self.student.project_interests = "recommender systems"
        self.student.is_assigned = False
        self.student.save()
        assigned = create_student(supervisor=self.supervisor)
        assigned.is_assigned = True
        assigned.save()
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse("student-interests"))
        ids = {row["student_id"] for row in response.data}
        self.assertIn(self.student.id, ids)
        self.assertNotIn(assigned.id, ids)

    def test_recommendation_uses_interests_and_expertise(self):
        match = create_supervisor()
        match.areas_of_expertise = "nlp, recommendation systems"
        match.save()
        other = create_supervisor()
        other.areas_of_expertise = "robotics"
        other.save()
        self.student.project_interests = "NLP-based recommendation systems"
        self.student.department = "Engineering"
        self.student.save()
        match.department = "Engineering"
        match.save()
        other.department = "Engineering"
        other.save()
        self.client.force_authenticate(self.admin)
        response = self.client.get(
            reverse("suggest-supervisor"),
            {"student_id": self.student.id},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["supervisor_id"] for item in response.data["candidates"]]
        self.assertEqual(ids[0], match.id)
        reasoning = response.data["candidates"][0]["reason_facts"][0]
        self.assertIn("recommendation systems", reasoning.lower())


class CohortBenchmarkTests(APITestCase):
    def setUp(self):
        self.supervisor = create_supervisor()
        self.session = create_session(is_active=True)

    def test_opted_out_student_gets_minimal_response(self):
        student = create_student(supervisor=self.supervisor)
        student.department = "Engineering"
        student.save()
        self.client.force_authenticate(student)
        response = self.client.get(reverse("cohort-benchmark"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["opted_in"])
        self.assertEqual(response.data["suppressed_reason"], "opt_out")

    def test_opted_in_with_small_cohort_is_suppressed(self):
        student = create_student(supervisor=self.supervisor)
        student.department = "Engineering"
        student.benchmark_opt_in = True
        student.save()
        for _ in range(3):
            other = create_student(supervisor=self.supervisor)
            other.department = "Engineering"
            other.save()
        self.client.force_authenticate(student)
        response = self.client.get(reverse("cohort-benchmark"))
        self.assertEqual(response.data["opted_in"], True)
        self.assertEqual(response.data["suppressed_reason"], "minimum_cohort_not_met")
        self.assertNotIn("aggregate", response.data)

    def test_opted_in_with_large_cohort_returns_aggregates_only(self):
        student = create_student(supervisor=self.supervisor)
        student.department = "Engineering"
        student.benchmark_opt_in = True
        student.save()
        for _ in range(5):
            other = create_student(supervisor=self.supervisor)
            other.department = "Engineering"
            other.save()
        self.client.force_authenticate(student)
        response = self.client.get(reverse("cohort-benchmark"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["suppressed_reason"], None)
        self.assertIn("caller_stage", response.data)
        self.assertIn("aggregate", response.data)
        flat = str(response.data)
        self.assertNotIn("@example.com", flat)
        self.assertNotIn(student.full_name, flat)
        self.assertNotIn(self.supervisor.full_name, flat)

    def test_non_student_denied(self):
        self.client.force_authenticate(self.supervisor)
        self.assertEqual(
            self.client.get(reverse("cohort-benchmark")).status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_preference_endpoint_validates_boolean(self):
        student = create_student(supervisor=self.supervisor)
        student.benchmark_opt_in = False
        student.save()
        self.client.force_authenticate(student)
        response = self.client.put(
            reverse("benchmark-preference"),
            {"benchmark_opt_in": "yes"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.put(
            reverse("benchmark-preference"),
            {"benchmark_opt_in": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        student.refresh_from_db()
        self.assertTrue(student.benchmark_opt_in)


class DefenseQuestionsTests(APITestCase):
    def setUp(self):
        self.supervisor = create_supervisor()
        self.student = create_student(supervisor=self.supervisor)
        self.other_student = create_student(supervisor=self.supervisor)
        self.project = create_project(student=self.student, supervisor=self.supervisor)
        self.submission = create_submission(
            project=self.project,
            milestone="chapter_one",
            version=1,
            extracted_text=(
                "Chapter One: Introduction\n"
                "The objective is to evaluate citation issues.\n"
                "We used a mixed method approach with quantitative results.\n"
                "Natural Language Processing drives the analysis."
            ),
            extraction_status="success",
        )
        create_review(
            submission=self.submission,
            reviewer=self.supervisor,
            feedback="Citation needs improvement and methodology is unclear.",
        )

    def test_student_receives_seeds(self):
        self.client.force_authenticate(self.student)
        response = self.client.get(reverse("defense-questions"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        categories = {seed["category"] for seed in response.data["seeds"]}
        self.assertIn("headings", categories)
        self.assertIn("objectives", categories)
        self.assertIn("methods", categories)
        self.assertIn("feedback_weak_point", categories)
        for seed in response.data["seeds"]:
            self.assertIn(seed["difficulty"], {"easy", "medium", "hard"})

    def test_other_student_does_not_leak(self):
        other_project = create_project(
            student=self.other_student, supervisor=self.supervisor
        )
        other_submission = create_submission(
            project=other_project,
            milestone="chapter_one",
            version=1,
            extracted_text="Confidential content",
            extraction_status="success",
        )
        create_review(
            submission=other_submission,
            reviewer=self.supervisor,
            feedback="Private feedback",
        )

        self.client.force_authenticate(self.student)
        response = self.client.get(reverse("defense-questions"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        flat = " ".join(seed["evidence"] for seed in response.data["seeds"])
        self.assertNotIn("Confidential content", flat)
        self.assertNotIn("Private feedback", flat)

    def test_supervisor_and_admin_denied(self):
        self.client.force_authenticate(self.supervisor)
        self.assertEqual(
            self.client.get(reverse("defense-questions")).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        admin = create_admin()
        self.client.force_authenticate(admin)
        self.assertEqual(
            self.client.get(reverse("defense-questions")).status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_invalid_filters_rejected(self):
        self.client.force_authenticate(self.student)
        response = self.client.get(
            reverse("defense-questions"),
            {"limit": 0},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.get(
            reverse("defense-questions"),
            {"milestone": "unknown"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.get(
            reverse("defense-questions"),
            {"difficulty": "extreme"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SuggestSupervisorTests(APITestCase):
    def setUp(self):
        from accounts.models import Tag

        self.admin = create_admin()
        self.admin.department = "Engineering"
        self.admin.save()
        self.student = create_student(supervisor=None, department="Engineering")
        self.tag_a = Tag.objects.create(name="nlp")
        self.tag_b = Tag.objects.create(name="vision")
        self.tag_c = Tag.objects.create(name="robotics")

        self.expert = create_supervisor()
        self.expert.expertise_tags.set([self.tag_a, self.tag_b])
        self.expert.capacity = 5
        self.expert.save()

        self.balanced = create_supervisor()
        self.balanced.expertise_tags.set([self.tag_a])
        self.balanced.capacity = 5
        self.balanced.save()

        self.outsider = create_supervisor()
        self.outsider.expertise_tags.set([self.tag_c])
        self.outsider.department = "Different"
        self.outsider.capacity = 5
        self.outsider.save()

        self.full = create_supervisor()
        self.full.expertise_tags.set([self.tag_a])
        self.full.capacity = 1
        self.full.save()
        create_student(supervisor=self.full)

        self.unapproved = create_supervisor(approved=False)
        self.unapproved.expertise_tags.set([self.tag_a])
        self.unapproved.capacity = 5
        self.unapproved.save()

        self.project = create_project(
            student=self.student, supervisor=None, session=None
        )
        self.project.tags.set([self.tag_a, self.tag_b])

    def test_admin_receives_scored_candidates(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(
            reverse("suggest-supervisor"),
            {"student_id": self.student.id},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["supervisor_id"] for item in response.data["candidates"]]
        self.assertIn(self.expert.id, ids)
        self.assertIn(self.balanced.id, ids)
        self.assertNotIn(self.outsider.id, ids)
        self.assertNotIn(self.unapproved.id, ids)
        self.assertNotIn(self.full.id, ids)
        self.assertGreaterEqual(
            response.data["candidates"][0]["total_score"],
            response.data["candidates"][-1]["total_score"],
        )

    def test_supervisor_mode_returns_matching_students(self):
        match = create_student()
        match.department = "Engineering"
        match.project_interests = "nlp, recommendation systems"
        match.is_assigned = False
        match.save()
        other = create_student()
        other.department = "Engineering"
        other.project_interests = "robotics"
        other.is_assigned = False
        other.save()
        supervisor = create_supervisor()
        supervisor.department = "Engineering"
        supervisor.areas_of_expertise = "nlp, recommendation systems"
        supervisor.save()

        self.client.force_authenticate(self.admin)
        response = self.client.get(
            reverse("suggest-supervisor"),
            {"supervisor_id": supervisor.id},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["mode"], "students_for_supervisor")
        ids = [item["student_id"] for item in response.data["candidates"]]
        self.assertEqual(ids[0], match.id)
        self.assertIn(
            "recommendation systems",
            response.data["candidates"][0]["reasoning"].lower(),
        )

    def test_supervisor_mode_rejects_full_supervisor(self):
        supervisor = create_supervisor(capacity=1)
        create_student(supervisor=supervisor)
        self.client.force_authenticate(self.admin)
        response = self.client.get(
            reverse("suggest-supervisor"),
            {"supervisor_id": supervisor.id},
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_recommendation_does_not_write(self):
        self.client.force_authenticate(self.admin)
        self.client.get(
            reverse("suggest-supervisor"),
            {"student_id": self.student.id},
        )
        self.student.refresh_from_db()
        self.assertIsNone(self.student.supervisor)

    def test_non_admin_is_denied(self):
        self.client.force_authenticate(self.balanced)
        response = self.client.get(
            reverse("suggest-supervisor"),
            {"student_id": self.student.id},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_limit_is_rejected(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(
            reverse("suggest-supervisor"),
            {"student_id": self.student.id, "limit": 0},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.get(
            reverse("suggest-supervisor"),
            {"student_id": self.student.id, "limit": 20},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class StalledStudentsTests(APITestCase):
    def setUp(self):
        self.admin = create_admin()
        self.supervisor = create_supervisor()
        self.other_supervisor = create_supervisor()

    def test_only_supervisor_and_admin_can_access(self):
        student = create_student(supervisor=self.supervisor)
        self.client.force_authenticate(student)
        response = self.client.get(reverse("stalled-students"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervisor_only_sees_assigned_students(self):
        own_student = create_student(supervisor=self.supervisor)
        other_student = create_student(supervisor=self.other_supervisor)
        old_date = timezone.now() - timedelta(days=60)
        own_student.date_joined = old_date
        own_student.save(update_fields=["date_joined"])
        other_student.date_joined = old_date
        other_student.save(update_fields=["date_joined"])

        self.client.force_authenticate(self.supervisor)
        response = self.client.get(reverse("stalled-students"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {item["student_id"] for item in response.data["results"]}
        self.assertIn(own_student.id, ids)
        self.assertNotIn(other_student.id, ids)

    def test_threshold_bounds(self):
        self.client.force_authenticate(self.supervisor)
        response = self.client.get(
            reverse("stalled-students"), {"threshold_days": 0}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.get(
            reverse("stalled-students"), {"threshold_days": 200}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.get(
            reverse("stalled-students"), {"threshold_days": "abc"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SubmissionDiffTests(APITestCase):
    def setUp(self):
        self.supervisor = create_supervisor()
        self.other_supervisor = create_supervisor()
        self.student = create_student(supervisor=self.supervisor)
        self.other_student = create_student(supervisor=self.other_supervisor)
        self.project = create_project(student=self.student, supervisor=self.supervisor)
        self.first = create_submission(
            project=self.project,
            milestone="chapter_one",
            version=1,
            extracted_text="Methodology is unclear. Citation needs improvement.",
            extraction_status="success",
        )
        self.second = create_submission(
            project=self.project,
            milestone="chapter_one",
            version=2,
            previous=self.first,
            extracted_text="Methodology now describes sampling and data sources. Citation still needs improvement.",
            extraction_status="success",
        )

    def test_diff_for_authorized_supervisor(self):
        create_review(submission=self.first, reviewer=self.supervisor, feedback="Citation needs improvement")
        create_review(submission=self.first, reviewer=self.supervisor, feedback="Methodology unclear")

        self.client.force_authenticate(self.supervisor)
        response = self.client.get(
            reverse("submission-diff", kwargs={"submission_id": self.second.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["comparison"]["id"], self.first.id)
        self.assertGreater(response.data["diff"]["word_count_delta"], 0)
        statuses = {item["status"] for item in response.data["feedback_coverage"]}
        self.assertTrue(statuses.issubset({"likely_addressed", "possibly_addressed", "not_evident"}))
        self.assertIn("Heuristic: supervisor must verify", " ".join(response.data["warnings"]))

    def test_diff_uses_default_previous_when_compare_to_omitted(self):
        self.client.force_authenticate(self.supervisor)
        response = self.client.get(
            reverse("submission-diff", kwargs={"submission_id": self.second.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["comparison"]["version"], 1)

    def test_diff_handles_identical_versions(self):
        third = create_submission(
            project=self.project,
            milestone="chapter_one",
            version=3,
            previous=self.second,
            extracted_text=self.second.extracted_text,
            extraction_status="success",
        )
        self.client.force_authenticate(self.supervisor)
        response = self.client.get(
            reverse("submission-diff", kwargs={"submission_id": third.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["diff"]["change_ratio"], 0.0)

    def test_first_version_returns_no_previous_warning(self):
        self.client.force_authenticate(self.supervisor)
        response = self.client.get(
            reverse("submission-diff", kwargs={"submission_id": self.first.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["comparison"], None)
        self.assertIn("first version", " ".join(response.data["warnings"]).lower())

    def test_cross_project_comparison_is_rejected(self):
        other_project = create_project(
            student=self.other_student, supervisor=self.other_supervisor
        )
        other_submission = create_submission(
            project=other_project,
            milestone="chapter_one",
            version=1,
            extracted_text="unrelated content",
            extraction_status="success",
        )

        self.client.force_authenticate(self.supervisor)
        response = self.client.get(
            reverse("submission-diff", kwargs={"submission_id": self.second.id}),
            {"compare_to": other_submission.id},
            format="json",
        )
        self.assertIn(response.status_code, (400, 403))

    def test_other_supervisor_is_forbidden(self):
        self.client.force_authenticate(self.other_supervisor)
        response = self.client.get(
            reverse("submission-diff", kwargs={"submission_id": self.second.id})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_extraction_failure_surfaces_warning(self):
        broken = create_submission(
            project=self.project,
            milestone="chapter_one",
            version=3,
            previous=self.second,
            extracted_text="",
            extraction_status="error",
        )
        self.client.force_authenticate(self.supervisor)
        response = self.client.get(
            reverse("submission-diff", kwargs={"submission_id": broken.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(
            "extraction was incomplete",
            " ".join(response.data["warnings"]).lower(),
        )


class RevisionHistoryTests(APITestCase):
    def test_duplicate_version_for_project_milestone_is_rejected(self):
        supervisor = create_supervisor()
        student = create_student(supervisor=supervisor)
        project = create_project(student=student, supervisor=supervisor)
        create_submission(project=project, milestone="proposal", version=1)

        with self.assertRaises(IntegrityError):
            Submission.objects.create(
                project=project, milestone="proposal", version=1
            )

    def test_submission_version_links_to_previous(self):
        supervisor = create_supervisor()
        student = create_student(supervisor=supervisor)
        project = create_project(student=student, supervisor=supervisor)
        first = create_submission(project=project, milestone="proposal", version=1)
        second = create_submission(
            project=project, milestone="proposal", version=2, previous=first
        )
        self.assertEqual(second.previous_id, first.id)

class PdfExtractionTests(APITestCase):
    """Unit coverage for the bounded PDF text-extraction service."""

    @staticmethod
    def _minimal_pdf(text):
        stream = f"BT /F1 12 Tf 72 712 Td ({text}) Tj ET".encode()
        content = (
            b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n"
            + stream + b"\nendstream"
        )
        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
            content,
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        ]
        out = b"%PDF-1.4\n"
        offsets = []
        for i, obj in enumerate(objects, 1):
            offsets.append(len(out))
            out += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
        xref = len(out)
        out += b"xref\n0 6\n0000000000 65535 f \n"
        for off in offsets:
            out += f"{off:010d} 00000 n \n".encode()
        out += (
            b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n"
            + str(xref).encode() + b"\n%%EOF\n"
        )
        return out

    def test_extracts_text_from_real_pdf(self):
        data = self._minimal_pdf("Hello World")
        text, status_, error = pdf_text.extract_pdf_text(
            SimpleUploadedFile("a.pdf", data, content_type="application/pdf")
        )
        self.assertEqual(status_, "success")
        self.assertIn("Hello World", text)
        self.assertEqual(error, "")

    def test_empty_pages_report_empty(self):
        data = self._minimal_pdf("Hello World")
        with patch.object(pdf_text.PdfReader, "pages", []):
            text, status_, error = pdf_text.extract_pdf_text(
                SimpleUploadedFile("a.pdf", data, content_type="application/pdf")
            )
        self.assertEqual(status_, "empty")

    def test_corrupt_pdf_reports_error(self):
        text, status_, error = pdf_text.extract_pdf_text(
            SimpleUploadedFile(
                "a.pdf", b"not a pdf at all", content_type="application/pdf"
            )
        )
        self.assertEqual(status_, "error")

    def test_page_limit_reports_too_large(self):
        data = self._minimal_pdf("Hello World")
        page = type("Page", (), {"extract_text": lambda self, **kw: "x"})()
        fake_reader = type(
            "Reader", (), {"pages": [page] * (pdf_text.MAX_PAGES + 1)}
        )()
        with patch.object(pdf_text, "PdfReader", lambda *a, **kw: fake_reader):
            text, status_, error = pdf_text.extract_pdf_text(
                SimpleUploadedFile("a.pdf", data, content_type="application/pdf")
            )
        self.assertEqual(status_, "too_large")

    def test_size_limit_reports_too_large(self):
        original_limit = pdf_text.MAX_BYTES
        try:
            pdf_text.MAX_BYTES = 4
            text, status_, error = pdf_text.extract_pdf_text(
                SimpleUploadedFile("a.pdf", b"12345", content_type="application/pdf")
            )
        finally:
            pdf_text.MAX_BYTES = original_limit
        self.assertEqual(status_, "too_large")

    def test_parser_failure_reports_error(self):
        data = self._minimal_pdf("Hello World")

        def boom(*args, **kwargs):
            raise RuntimeError("parser exploded")

        with patch.object(pdf_text, "PdfReader", boom):
            text, status_, error = pdf_text.extract_pdf_text(
                SimpleUploadedFile("a.pdf", data, content_type="application/pdf")
            )
        self.assertEqual(status_, "error")


class SerializerContractTests(APITestCase):
    """Regression: existing project/submission payloads remain usable."""

    def setUp(self):
        self.admin = create_admin()
        self.supervisor = create_supervisor()
        self.student = create_student(supervisor=self.supervisor)
        self.session = create_session(is_active=True)
        self.project = create_project(
            student=self.student, supervisor=self.supervisor, session=self.session
        )
        self.submission = create_submission(
            project=self.project,
            milestone="proposal",
            version=1,
            extracted_text="chapter text",
            extraction_status="success",
        )

    def test_project_list_contract(self):
        self.client.force_authenticate(self.student)
        response = self.client.get(reverse("projects-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        record = next(p for p in response.data if p["id"] == self.project.id)
        self.assertIn("title", record)
        self.assertIn("status", record)
        self.assertIn("session", record)

    def test_submission_list_contract(self):
        self.client.force_authenticate(self.student)
        response = self.client.get(reverse("submissions-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        record = next(s for s in response.data if s["id"] == self.submission.id)
        self.assertIn("milestone", record)
        self.assertIn("version", record)
        self.assertIn("file_url", record)
        self.assertIn("extraction_status", record)
        self.assertEqual(record["extraction_status"], "success")

class ProjectSessionLinkageTests(APITestCase):
    def test_create_project_assigns_active_session(self):
        active = create_session(is_active=True)
        supervisor = create_supervisor()
        student = create_student(supervisor=supervisor)

        self.client.force_authenticate(student)
        response = self.client.post(
            reverse("create-project"),
            {"title": "NLP project", "description": "About NLP"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        project = Project.objects.get(id=response.data["project"]["id"])
        self.assertEqual(project.session_id, active.id)
