from django.urls import path

from .views import LoginView, RegistrationView

urlpatterns = [
    path("auth/register/", RegistrationView.as_view(), name="auth-register"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
]
