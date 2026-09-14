"""users serializer"""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Users


# ========================
# Registeration Serializers
# ========================
class UserRegisterRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = [
            "username",
            "email",
            "password",
        ]
        extra_kwargs = {"password": {"write_only": True}}


class UserRegisterResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = [
            "id",
            "username",
            "email",
        ]


# ========================
# GET Me Serializers
# ========================
class UserMeResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ["id", "username", "email", "last_login"]


# ========================
# PATCH User Serializers
# ========================
class UserUpdateResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ["username", "password", "email", "last_login"]
        extra_kwargs = {"password": {"write_only": True}}


# ========================
# Token Custome Serializers
# ========================
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token["username"] = user.username
        # ...

        return token
