from django.shortcuts import render
from rest_framework import generics, permissions
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import status, viewsets
from rest_framework.response import Response
from .serializers import UserSerializer, LoginSerializer, SupervisorSerializer, AssignSupervisorSerializer, StudentSerializer, StudentWithSupervisorSerializer
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
def approved_supervisors(request):
    supervisors = User.objects.filter(role="supervisor", is_approved=True, is_fully_booked=False)
    serializer = SupervisorSerializer(supervisors, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def pending_supervisors(request):
    supervisors = User.objects.filter(role="supervisor", is_approved=False)
    serializer = SupervisorSerializer(supervisors, many=True)
    return Response(serializer.data)

# all students
@api_view(["GET"])
def unassigned_students(request):
    students = User.objects.filter(role="student", is_assigned=False)
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
    



# class SupervisorViewSet(viewsets.ModelViewSet):
#     queryset = Supervisor.objects.all()
#     serializer_class = SupervisorSerializer
#     permission_classes = [IsAdminRole]  # or per-action permissions

#     @action(detail=True, methods=["post"], url_path="assign-students")
#     def assign_students(self, request, pk=None):
#         # pk = supervisor id from URL
#         data = request.data.copy()
#         data["supervisor_id"] = pk  # enforce supervisor from URL

#         serializer = AssignSupervisorSerializer(data=data)
#         if serializer.is_valid():
#             students = serializer.save()
#             supervisor = serializer.validated_data["supervisor"]

#             return Response({
#                 "message": "Supervisor assigned successfully.",
#                 "supervisor": supervisor.full_name,
#                 "students_assigned": [s.full_name for s in students],
#             }, status=status.HTTP_200_OK)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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

    def get(self, request, supervisor_id):
        supervisor = User.objects.filter(id=supervisor_id, role='supervisor').first()

        if not supervisor:
            return Response({"error": "Supervisor not found"}, status=404)

        students = supervisor.students_under_supervision.all()
        serializer = StudentSerializer(students, many=True)

        return Response(serializer.data)