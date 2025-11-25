# from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ProjectSessionSerializer
from .models import ProjectSession

class ProjectSessionView(APIView):

    def get(self, request):
        sessions = ProjectSession.objects.all().order_by('-created_at')
        serializer = ProjectSessionSerializer(sessions, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ProjectSessionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Session created successfully", "data": serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

