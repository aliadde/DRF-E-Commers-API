from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from django_ecommers.apps.users.models import Users
from django_ecommers.apps.users.serializer import (
    UserMeResponseSerializer,
    UserRegisterRequestSerializer,
    UserRegisterResponseSerializer,
    UserResetPasswordSerializer,
    UserUpdateResponseSerializer,
)
from django_ecommers.apps.users.services import UserService


class UserPublicView(APIView):
    """View for User operation."""

    def post(self, request):
        """Register new user."""
        serializer = UserRegisterRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_service = UserService()

        user = user_service.create_user(
            user_data=serializer.validated_data,
        )

        response_serializer = UserRegisterResponseSerializer(user)

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class UserPrivateView(APIView):
    # jwt token and Authorization header is require for this class view
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """User Get itself data"""
        serializer = UserMeResponseSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        """User update itself data"""
        # request.user is exactly the authenticated user object of class users.Users
        # partial: if true, the fields are optional (not require)
        serializer = UserUpdateResponseSerializer(
            request.user, data=request.data, partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserPasswordResetView(APIView):
    """Reset user password"""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        # serializer
        serializer = UserResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        user = request.user
        if user.check_password(data["current_password"]):
            # change password to new one
            user.set_password(data["new_password"])
            user.save()

            return Response({"message": "Your password reset successfully."})
        return Response(
            {"error": "Your current_password is incorrect."},
            status=status.HTTP_400_BAD_REQUEST,
        )
