from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.factories import (
    create_admin,
    create_student,
    create_supervisor,
)
from projects.factories import create_project, create_submission


class LoginRefreshTests(APITestCase):
    def test_student_login_succeeds(self):
        create_student(email="alice@example.com", full_name="Alice")
        response = self.client.post(
            reverse("user-login"),
            {"email": "alice@example.com", "password": "pass-test-123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["role"], "student")

    def test_pending_supervisor_cannot_login(self):
        create_supervisor(
            approved=False, email="sup@example.com", full_name="Supervisor"
        )
        response = self.client.post(
            reverse("user-login"),
            {"email": "sup@example.com", "password": "pass-test-123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_refresh_returns_new_access_token(self):
        create_student(email="bob@example.com", full_name="Bob")
        login = self.client.post(
            reverse("user-login"),
            {"email": "bob@example.com", "password": "pass-test-123"},
            format="json",
        )
        refresh = login.data["refresh"]
        response = self.client.post(
            reverse("token-refresh"), {"refresh": refresh}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
class ProjectSubmissionScopeTests(APITestCase):
    def setUp(self):
        self.admin = create_admin()
        self.sup_a = create_supervisor()
        self.sup_b = create_supervisor()
        self.student_a = create_student(supervisor=self.sup_a)
        self.student_b = create_student(supervisor=self.sup_b)
        self.project_a = create_project(
            student=self.student_a, supervisor=self.sup_a, title="Project A"
        )
        self.project_b = create_project(
            student=self.student_b, supervisor=self.sup_b, title="Project B"
        )
        self.sub_a = create_submission(project=self.project_a)
        self.sub_b = create_submission(project=self.project_b)

    def test_student_sees_only_own_projects(self):
        self.client.force_authenticate(self.student_a)
        response = self.client.get(reverse("projects-list"))
        ids = [p["id"] for p in response.data]
        self.assertEqual(ids, [self.project_a.id])

    def test_supervisor_sees_only_own_projects(self):
        self.client.force_authenticate(self.sup_a)
        response = self.client.get(reverse("projects-list"))
        ids = [p["id"] for p in response.data]
        self.assertEqual(ids, [self.project_a.id])

    def test_admin_sees_all_projects(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse("projects-list"))
        ids = [p["id"] for p in response.data]
        self.assertEqual(
            sorted(ids), sorted([self.project_a.id, self.project_b.id])
        )

    def test_student_sees_only_own_submissions(self):
        self.client.force_authenticate(self.student_a)
        response = self.client.get(reverse("submissions-list"))
        ids = [s["id"] for s in response.data]
        self.assertEqual(ids, [self.sub_a.id])

    def test_supervisor_sees_only_own_submissions(self):
        self.client.force_authenticate(self.sup_a)
        response = self.client.get(reverse("submissions-list"))
        ids = [s["id"] for s in response.data]
        self.assertEqual(ids, [self.sub_a.id])


class CrossAccessTests(APITestCase):
    def setUp(self):
        self.admin = create_admin()
        self.sup_a = create_supervisor()
        self.sup_b = create_supervisor()
        self.student_a = create_student(supervisor=self.sup_a)
        self.student_b = create_student(supervisor=self.sup_b)

    def test_supervisor_cannot_view_another_supervisors_students(self):
        self.client.force_authenticate(self.sup_a)
        response = self.client.get(f"/api/supervisors/{self.sup_b.id}/students/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervisor_can_view_own_students(self):
        self.client.force_authenticate(self.sup_a)
        response = self.client.get(f"/api/supervisors/{self.sup_a.id}/students/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [s["id"] for s in response.data]
        self.assertEqual(ids, [self.student_a.id])

    def test_admin_can_view_any_supervisors_students(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(f"/api/supervisors/{self.sup_b.id}/students/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_student_cannot_access_any_supervisors_students(self):
        self.client.force_authenticate(self.student_a)
        response = self.client.get(f"/api/supervisors/{self.sup_a.id}/students/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cannot_view_another_students_record(self):
        self.client.force_authenticate(self.student_a)
        response = self.client.get(
            reverse("students-detail", kwargs={"student_id": self.student_b.id})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_student_can_view_own_record(self):
        self.client.force_authenticate(self.student_a)
        response = self.client.get(
            reverse("students-detail", kwargs={"student_id": self.student_a.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_supervisor_cannot_view_unrelated_student_record(self):
        self.client.force_authenticate(self.sup_b)
        response = self.client.get(
            reverse("students-detail", kwargs={"student_id": self.student_a.id})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AuthMeTests(APITestCase):
    def setUp(self):
        self.admin = create_admin()
        self.supervisor = create_supervisor()
        self.student = create_student()

    def test_authenticated_user_gets_own_identity(self):
        self.client.force_authenticate(self.student)
        response = self.client.get(reverse("auth-me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.student.id)
        self.assertEqual(response.data["role"], "student")

    def test_identity_matches_server_role_not_client_input(self):
        self.client.force_authenticate(self.supervisor)
        response = self.client.get(reverse("auth-me"))
        self.assertEqual(response.data["role"], "supervisor")

    def test_anonymous_is_denied(self):
        response = self.client.get(reverse("auth-me"))
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )
