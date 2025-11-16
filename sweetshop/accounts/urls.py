from django.urls import path

from .views import LoginView, RegistrationView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("auth/register/", RegistrationView.as_view(), name="auth-register"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    # Allow clients to exchange a valid refresh token for a new access token.
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
