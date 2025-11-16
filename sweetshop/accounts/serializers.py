"""Serializers encapsulating auth-related validation and output."""

from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Public-facing user representation for API responses."""

    class Meta:
        model = User
        fields = ("id", "username", "name", "email", "role")
        read_only_fields = fields


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Validates signup data (name + email) and hashes passwords when creating users."""

    name = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("name", "email", "password")

    def create(self, validated_data):
        name = validated_data.pop("name")
        email = validated_data["email"].lower()
        username = self._generate_username(name=name, email=email)

        user_data = {
            **validated_data,
            "username": username,
            "name": name,
            "email": email,
            "role": User.Role.CUSTOMER,
        }
        return User.objects.create_user(**user_data)

    def _generate_username(self, *, name: str, email: str) -> str:
        from django.utils.text import slugify

        base_slug = slugify(name) or email.split("@")[0]
        base_slug = base_slug or "user"
        base_slug = base_slug[:150]
        candidate = base_slug
        suffix = 1

        while User.objects.filter(username=candidate).exists():
            suffix += 1
            trimmed_base = base_slug[: max(0, 150 - len(f"-{suffix}"))]
            candidate = f"{trimmed_base}-{suffix}" if trimmed_base else f"user-{suffix}"
        return candidate


class LoginSerializer(serializers.Serializer):
    """Authenticate a user via email plus password."""

    email = serializers.EmailField(required=False)
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
