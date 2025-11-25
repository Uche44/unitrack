from rest_framework import serializers
from .models import ProjectSession

class ProjectSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectSession
        fields = ['id', 'session', 'duration', 'start_date', 'end_date', 'created_at']
