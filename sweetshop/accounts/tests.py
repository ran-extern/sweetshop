"""TDD-first tests for the authentication API endpoints."""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class AuthAPITests(APITestCase):
	def test_can_register_user_and_receive_tokens(self) -> None:
		url = reverse("auth-register")
		payload = {
			"username": "sweetlover",
			"email": "sweetlover@example.com",
			"password": "sekretpass123",
		}

		# Happy-path registration should yield a persisted user plus JWT pair.
		response = self.client.post(url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertIn("user", response.data)
		self.assertEqual(response.data["user"]["email"], payload["email"])
		self.assertEqual(response.data["user"]["username"], payload["username"])
		self.assertIn("tokens", response.data)
		self.assertIn("access", response.data["tokens"])
		self.assertIn("refresh", response.data["tokens"])

	def test_can_login_and_get_fresh_tokens(self) -> None:
		user_model = get_user_model()
		user_model.objects.create_user(
			username="admin",
			email="admin@example.com",
			password="strongpass123",
			role="admin",
		)

		url = reverse("auth-login")
		payload = {"email": "admin@example.com", "password": "strongpass123"}

		response = self.client.post(url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn("tokens", response.data)
		self.assertIn("access", response.data["tokens"])
		self.assertIn("refresh", response.data["tokens"])

	def test_admin_login_returns_admin_role(self) -> None:
		user_model = get_user_model()
		admin_user = user_model.objects.create_user(
			username="sugar-boss",
			email="boss@example.com",
			password="supersecret",
			role="admin",
		)

		url = reverse("auth-login")
		# Admins should receive their role in the payload so the UI can gate views.
		payload = {"email": admin_user.email, "password": "supersecret"}

		# Registration must echo the same email casing back to the caller.
		response = self.client.post(url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["user"]["role"], "admin")
		self.assertIn("access", response.data["tokens"])
		self.assertIn("refresh", response.data["tokens"])

	def test_can_register_with_email_and_username(self) -> None:
		url = reverse("auth-register")
		payload = {
			"username": "emailfan",
			"email": "emailfan@example.com",
			"password": "emailsrock123",
		}

		response = self.client.post(url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(response.data["user"]["email"], payload["email"])
		self.assertIn("access", response.data["tokens"])
		self.assertIn("refresh", response.data["tokens"])

	def test_can_login_and_check_role_for_customer(self) -> None:
		user_model = get_user_model()
		user_model.objects.create_user(
			username="choco-chief",
			email="choco@example.com",
			password="emailpass321",
		)

		url = reverse("auth-login")
		# Email-only login route exercises the custom authentication backend.
		payload = {"email": "choco@example.com", "password": "emailpass321"}

		response = self.client.post(url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["user"]["email"], "choco@example.com")
		self.assertIn("access", response.data["tokens"])
		self.assertIn("refresh", response.data["tokens"])
		self.assertEqual(response.data["user"]["role"], "customer")
