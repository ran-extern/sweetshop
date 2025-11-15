"""Authentication endpoints for registration and login."""

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import LoginSerializer, UserRegistrationSerializer, UserSerializer


def _generate_tokens(user):
	"""Create a fresh refresh/access token pair for the given user."""
	refresh = RefreshToken.for_user(user)
	# SimpleJWT keeps the access token on the RefreshToken instance so we can
	# serialize both without having to hit the database twice.
	return {"refresh": str(refresh), "access": str(refresh.access_token)}


class RegistrationView(APIView):
	permission_classes = [permissions.AllowAny]

	def post(self, request):
		"""Validate incoming signup data and return the new user plus tokens."""
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
		"""Accept username or email credentials and respond with JWTs."""
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
