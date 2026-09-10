"""users serializer"""

from rest_framework import serializers

from .models import Users


# ========================
# Registeration Serializers
# ========================
class UserRegisterRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = [
            "name",
            "email",
            "password",
        ]
        extra_kwargs = {"password": {"write_only": True}}


class UserRegisterResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = [
            "id",
            "name",
            "email",
        ]
