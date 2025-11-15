from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class EmailBackend(ModelBackend):
    """
    Custom authentication backend that allows users to log in using their email address.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        email=kwargs.get("email",username)
        if email is None or password is None:
            return None
        user=User.objects.filter(email__iexact=email).first()
        if user and user.check_password(password):
            return user
        return None