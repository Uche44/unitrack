from django.urls import path
from .views import ProjectSessionView

urlpatterns = [
    path("session/", ProjectSessionView.as_view(), name="project-session"),
]
