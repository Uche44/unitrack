from rest_framework import serializers
from .models import ProjectSession, Project, Submission

class ProjectSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectSession
        fields = ['id', 'session', 'duration', 'start_date', 'end_date', 'created_at']



class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            'id',
            'student',
            'supervisor',
            'title',
            'description',
            'status',
            'created_at'
        ]
        read_only_fields = ['id', 'status', 'created_at']


# return projects
class ProjectSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    supervisor_name = serializers.CharField(source='supervisor.get_full_name', read_only=True)

    class Meta:
        model = Project
        fields = [
            'id',
            'student',
            'student_name',
            'supervisor',
            'supervisor_name',
            'title',
            'description',
            'status',
            'created_at',
            'updated_at'
        ]


class SubmissionCreateSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)
    unique_together = ('project', 'milestone', 'version')
    class Meta:
        model = Submission
        fields = [
            'id',
            'project',
            'milestone',
            'file',
            'comment',
            'submitted_at'
        ]
        read_only_fields = ['id', 'submitted_at']



# return submissions
class SubmissionSerializer(serializers.ModelSerializer):
    project_title = serializers.CharField(source='project.title', read_only=True)

    class Meta:
        model = Submission
        fields = [
            'id',
            'project',
            'project_title',
            'milestone',
            'file_url',
            'version',
            'comment',
            'is_read',
            'submitted_at'
        ]


class ProjectDetailSerializer(ProjectSerializer):
    submissions = SubmissionSerializer(many=True, read_only=True)

    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + ['submissions']

