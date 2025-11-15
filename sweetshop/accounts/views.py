"""Authentication endpoints for registration and login."""

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import LoginSerializer, UserRegistrationSerializer, UserSerializer


def _generate_tokens(user):
	refresh = RefreshToken.for_user(user)
	return {"refresh": str(refresh), "access": str(refresh.access_token)}


class RegistrationView(APIView):
	permission_classes = [permissions.AllowAny]

	def post(self, request):
		serializer = UserRegistrationSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		user = serializer.save()
		return Response(
			{
				"user": UserSerializer(user).data,
				"tokens": _generate_tokens(user),
			},
			status=status.HTTP_201_CREATED,
		)


class LoginView(APIView):
	permission_classes = [permissions.AllowAny]

	def post(self, request):
		serializer = LoginSerializer(data=request.data, context={"request": request})
		serializer.is_valid(raise_exception=True)
		user = serializer.validated_data["user"]
		return Response(
			{
				"user": UserSerializer(user).data,
				"tokens": _generate_tokens(user),
			},
			status=status.HTTP_200_OK,
		)
