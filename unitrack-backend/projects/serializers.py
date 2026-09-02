from rest_framework import serializers
from django.utils import timezone
from accounts.models import User
from .models import (
    ProjectSession,
    Project,
    Submission,
    SupervisorContact,
    SubmissionReview,
)

class ProjectSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectSession
        fields = ['id', 'session', 'duration', 'start_date', 'end_date', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']



class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            'id',
            'student',
            'supervisor',
            'session',
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
    tags = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='name'
    )

    class Meta:
        model = Project
        fields = [
            'id',
            'student',
            'student_name',
            'supervisor',
            'supervisor_name',
            'session',
            'tags',
            'title',
            'description',
            'status',
            'created_at',
            'updated_at'
        ]


class SubmissionCreateSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)
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
            'previous',
            'comment',
            'is_read',
            'is_approved',
            'is_rejected',
            'rejection_comment',
            'extraction_status',
            'submitted_at'
        ]


class ProjectDetailSerializer(ProjectSerializer):
    submissions = SubmissionSerializer(many=True, read_only=True)

    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + ['submissions']


class ProposalActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    comment = serializers.CharField(required=False, allow_blank=True)


class SupervisorContactCreateSerializer(serializers.ModelSerializer):
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='student', write_only=True
    )
    occurred_at = serializers.DateTimeField(required=False)

    class Meta:
        model = SupervisorContact
        fields = [
            'id',
            'student_id',
            'session',
            'contact_type',
            'note',
            'occurred_at',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def validate(self, attrs):
        student = attrs['student']
        supervisor = self.context.get('supervisor')
        if supervisor is None:
            raise serializers.ValidationError("Supervisor is required.")
        if student.role != 'student' or student.supervisor_id != supervisor.id:
            raise serializers.ValidationError(
                "Contact can only be logged for a student under this supervisor."
            )
        attrs['supervisor'] = supervisor
        attrs.setdefault('occurred_at', timezone.now())
        return attrs


class SupervisorContactSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)

    class Meta:
        model = SupervisorContact
        fields = [
            'id',
            'student',
            'student_name',
            'session',
            'contact_type',
            'note',
            'occurred_at',
            'created_at',
        ]


class SubmissionReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source='reviewer.full_name', read_only=True)

    class Meta:
        model = SubmissionReview
        fields = [
            'id',
            'submission',
            'reviewer',
            'reviewer_name',
            'decision',
            'feedback',
            'reviewed_at',
        ]

