"""Accounts domain models for authentication and authorization helpers."""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
	"""Extend Django's base user to capture Sweet Shop-specific roles."""

	class Role(models.TextChoices):
		"""Enumerate the supported access levels within the platform."""
		CUSTOMER = "customer", _("Customer")
		ADMIN = "admin", _("Admin")

	role = models.CharField(
		max_length=20,
		choices=Role.choices,
		default=Role.CUSTOMER,
		help_text="Determines the user's access level.",
	)

	def is_admin(self) -> bool:
		"""Convenience flag for permission checks."""
		return self.role == self.Role.ADMIN or self.is_staff or self.is_superuser

	def __str__(self) -> str:
		"""Display the username and human-friendly role in admin lists."""
		return f"{self.username} ({self.get_role_display()})"
