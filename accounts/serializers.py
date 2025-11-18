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
