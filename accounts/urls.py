from django.urls import path
from .views import UserSignupView, LoginView, RefreshTokenView, LogoutView, approved_supervisors, pending_supervisors, ApproveSupervisorView, AssignSupervisorView, unassigned_students, assigned_students, SupervisorStudentsView, StudentDetailView
from . import views


urlpatterns = [
    path('signup/', UserSignupView.as_view(), name='user-signup'),
    path('login/', LoginView.as_view(), name='user-login'),
    # path('guest-login/', GuestLoginView.as_view(), name='guest-login'),
    path('refresh/', RefreshTokenView.as_view(), name='token-refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path("supervisors/", approved_supervisors, name="approved-supervisors"),
    path("pending/", pending_supervisors, name="pending-supervisors"),
    path("students/", unassigned_students, name="all-students-data"),
    path("assigned-students/", assigned_students, name="assigned-students-data"),
    path(
        "supervisors/<int:supervisor_id>/approve/",
        ApproveSupervisorView.as_view(),
        name="approve-supervisor"
    ),
    path("assign-supervisor/", AssignSupervisorView.as_view(), name="assign-supervisor"),
    path("supervisors/<int:supervisor_id>/students/", SupervisorStudentsView.as_view()),
    path("supervisors/<int:supervisor_id>/students/<int:student_id>/", SupervisorStudentsView.as_view()),
    path('students/<int:student_id>/', StudentDetailView.as_view(), name='students-detail')

]
