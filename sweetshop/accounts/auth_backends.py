from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class EmailBackend(ModelBackend):
    """
    Custom authentication backend that allows users to log in using their email address.
    """

    def authenticate(self, request, email=None, password=None, **kwargs):
        User = get_user_model()
        if email is None:
            # DRF serializers sometimes pass credentials via "username"
            # so we gracefully fall back to that key for compatibility.
            email = kwargs.get("username")
        if email is None or password is None:
            return None
        try:
            user=User.objects.filter(email__iexact=email).first()
        except User.DoesNotExist:
            return None
        if user and user.check_password(password):
                return user
        return None