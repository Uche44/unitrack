from rest_framework import serializers
from .models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)

    class Meta:
        model = User
        fields = ['full_name', 'email', 'password', 'role', 'department', 'matric_no', 'staff_id']

    def create(self, validated_data):
        password = validated_data.pop('password')
        role = validated_data.get("role")

        if role == "supervisor":
            validated_data["is_approved"] = False
        else:
            validated_data["is_approved"] = True

        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        return user


class LoginSerializer(TokenObtainPairSerializer):
    username_field = 'email'  

    def validate(self, attrs):
        
        data = super().validate(attrs)

        # Supervisor approval check
        if self.user.role == "supervisor" and not self.user.is_approved:
            raise serializers.ValidationError("Your account is pending approval by an admin.")

        #user info in response
        data.update({
            "email": self.user.email,
            "role": self.user.role,
            "full_name": self.user.full_name,
        })
        return data
    

    # supervisor serial

class SupervisorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "full_name", "email", "staff_id", "department", "is_approved", "created_at"]


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'matric_no']

class AssignSupervisorSerializer(serializers.Serializer):
    student_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        max_length=5,  # <-- LIMIT TO 5 STUDENTS
    )
    supervisor_id = serializers.IntegerField()

    def validate(self, data):
        student_ids = data["student_ids"]
        supervisor_id = data["supervisor_id"]

        # Fetch supervisor
        try:
            supervisor = User.objects.get(id=supervisor_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("Supervisor not found.")

        # Validate supervisor
        if supervisor.role != "supervisor":
            raise serializers.ValidationError("Selected user is not a supervisor.")


        # Prevent supervisor overload
        if supervisor.students_under_supervision.count() + len(student_ids) > 10:
            raise serializers.ValidationError(
                f"{supervisor.full_name} cannot take more than 10 students total."
            )

        # Validate students
        students = []
        for sid in student_ids:
            try:
                student = User.objects.get(id=sid)
            except User.DoesNotExist:
                raise serializers.ValidationError(f"Student with ID {sid} does not exist.")

            if student.role != "student":
                raise serializers.ValidationError(f"User {sid} is not a student.")

            if student.supervisor_id is not None:
                raise serializers.ValidationError(
                    f"Student {student.full_name} is already assigned to a supervisor."
                )

            students.append(student)

        # Save  data
        data["supervisor"] = supervisor
        data["students"] = students
        return data

    def save(self):
        supervisor = self.validated_data["supervisor"]
        students = self.validated_data["students"]

        for student in students:
            student.supervisor = supervisor
            student.save()

        return students
