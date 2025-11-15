"""Serializers encapsulating auth-related validation and output."""

from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Public-facing user representation for API responses."""

    class Meta:
        model = User
        fields = ("id", "username", "email", "role")
        read_only_fields = fields


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Validates signup data and hashes passwords when creating users."""

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("username", "email", "password")

    def create(self, validated_data):
        validated_data["role"] = User.Role.CUSTOMER
        validated_data["email"] = validated_data["email"].lower()
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """Authenticate a user via username/email plus password."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        request = self.context.get("request")
        email = attrs.get("email")
        password = attrs.get("password")

        if not email:
            raise serializers.ValidationError({"detail": _("Email is required.")})

        if email:
            email = email.lower()

        user = authenticate(
            request=request,
            password=password,
            email=email,
        )

        if not user:
            raise serializers.ValidationError({"detail": _("Invalid credentials.")})

        attrs["user"] = user
        return attrs
