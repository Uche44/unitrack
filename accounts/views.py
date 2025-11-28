from django.shortcuts import render
from rest_framework import generics, permissions
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import status, viewsets
from rest_framework.response import Response
from .serializers import UserSerializer, LoginSerializer, SupervisorSerializer, AssignSupervisorSerializer, StudentSerializer, StudentWithSupervisorSerializer
from datetime import timedelta
import uuid
from .models import User
from rest_framework_simplejwt.views import TokenObtainPairView
from .is_admin import IsAdminRole

class UserSignupView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    queryset = User.objects.all()
    serializer_class = UserSerializer
     



class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user

        # Generate tokens manually
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = Response(
            {"message": "Login successful",
               "user": {
            "id": user.id, 
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name,
            "staff_id": user.staff_id, 
            "matric_no": user.matric_no,
            "is_approved": user.is_approved,
        }
             },
            status=status.HTTP_200_OK
        )

        # Set HttpOnly cookies
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,   
            samesite='Lax',
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,   
            samesite='Lax',
        )

        response.data.pop('access', None)
        response.data.pop('refresh', None)

        return response
    


# token refresh

class RefreshTokenView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response({"error": "Refresh token not provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh = RefreshToken(refresh_token)
            new_access_token = str(refresh.access_token)

            response = Response({"message": "Token refreshed"}, status=status.HTTP_200_OK)
            response.set_cookie(
                key="access_token",
                value=new_access_token,
                httponly=True,
                secure=False,
                samesite='Lax',
            )
            return response

        except TokenError:
            return Response({"error": "Invalid refresh token"}, status=status.HTTP_401_UNAUTHORIZED)

     
    
    # logout

class LogoutView(APIView):
    def post(self, request):
        response = Response({"message": "Logged out"}, status=status.HTTP_200_OK)
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response    


@api_view(["GET"])
def approved_supervisors(_request):
    supervisors = User.objects.filter(role="supervisor", is_approved=True, is_fully_booked=False)
    serializer = SupervisorSerializer(supervisors, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def pending_supervisors(_request):
    supervisors = User.objects.filter(role="supervisor", is_approved=False)
    serializer = SupervisorSerializer(supervisors, many=True)
    return Response(serializer.data)

# all students
@api_view(["GET"])
def unassigned_students(_request):
    students = User.objects.filter(role="student", is_assigned=False, is_guest=False)
    serializer = StudentSerializer(students, many=True)
    return Response(serializer.data)

# assigned students
@api_view(["GET"])
def assigned_students(request):
    students = User.objects.filter(role="student", is_assigned=True)
    serializer = StudentWithSupervisorSerializer(students, many=True)
    return Response(serializer.data)

# approval

class ApproveSupervisorView(APIView):
    permission_classes = [IsAdminRole]  

    def post(self, request, supervisor_id):
        try:
            supervisor = User.objects.get(id=supervisor_id)
        except User.DoesNotExist:
            return Response(
                {"error": "Supervisor not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if supervisor.role != "supervisor":
            return Response(
                {"error": "Only supervisors can be approved"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if supervisor.is_approved:
            return Response(
                {"message": "Supervisor is already approved"},
                status=status.HTTP_200_OK
            )

        supervisor.is_approved = True
        supervisor.save()

        return Response(
            {
                "message": f"{supervisor.full_name} has been approved successfully.",
                "supervisor": SupervisorSerializer(supervisor).data
            },
            status=status.HTTP_200_OK
        )
    

class AssignSupervisorView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request):
        serializer = AssignSupervisorSerializer(data=request.data)

        if serializer.is_valid():
            students = serializer.save()  
            supervisor = serializer.validated_data["supervisor"]

            return Response({
                "message": "Supervisor assigned successfully.",
                "supervisor": supervisor.full_name,
                "students_assigned": [s.full_name for s in students]
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 

# view for supervisors and students under them.

class SupervisorStudentsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, supervisor_id, student_id=None):
        supervisor = User.objects.filter(id=supervisor_id, role='supervisor').first()

        if not supervisor:
            return Response({"error": "Supervisor not found"}, status=404)

        students = supervisor.students_under_supervision.all()

        if student_id:
            student = students.filter(id=student_id).first()
            if not student:
                return Response({"error": "Student not found under this supervisor"}, status=404)
            serializer = StudentWithSupervisorSerializer(student)
            return Response(serializer.data)


        serializer = StudentSerializer(students, many=True)

        return Response(serializer.data)
    
    # get student details (with supervisor)


class StudentDetailView(RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = StudentWithSupervisorSerializer
    lookup_field = "id"          
    lookup_url_kwarg = "student_id"


class GuestLoginView(APIView):
    """
    Guest login endpoint.
    Creates a temporary guest user for demo purposes with specified role.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        role = request.data.get("role", "student")

        if role not in ["student", "supervisor", "admin"]:
            return Response(
                {"error": "Invalid role. Must be: student, supervisor, or admin"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Check if guest user for this role already exists
            guest_user = User.objects.filter(
                email=f"guest_{role}@demo.local",
                is_guest=True,
                role=role
            ).first()

            if not guest_user:
                # Create new guest user
                guest_email = f"guest_{role}@demo.local"
                guest_user = User.objects.create_user(
                    email=guest_email,
                    password=str(uuid.uuid4()),
                    full_name=f"Guest {role.capitalize()}",
                    role=role,
                    is_guest=True,
                    is_approved=True
                )

            # Generate tokens
            refresh = RefreshToken.for_user(guest_user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            response = Response(
                {
                    "message": "Guest login successful",
                    "user": {
                        "id": guest_user.id,
                        "email": guest_user.email,
                        "role": guest_user.role,
                        "full_name": guest_user.full_name,
                        "is_guest": True,
                        "is_approved": guest_user.is_approved,
                    },
                },
                status=status.HTTP_200_OK
            )

            # Set HttpOnly cookies
            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                secure=False,
                samesite='Lax',
            )
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=False,
                samesite='Lax',
            )

            return response

        except Exception as e:
            return Response(
                {"error": f"Guest login failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
