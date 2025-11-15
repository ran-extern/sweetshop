"""TDD-first API tests for sweets CRUD and inventory actions."""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Sweet


class SweetAPITests(APITestCase):
	def setUp(self) -> None:
		user_model = get_user_model()
		self.admin = user_model.objects.create_user(
			username="shop-admin",
			email="admin@sweets.test",
			password="supersecret",
			role="admin",
		)
		self.customer = user_model.objects.create_user(
			username="choco-fan",
			email="fan@sweets.test",
			password="sweetsecret",
			role="customer",
		)

		self.sample_sweet = Sweet.objects.create(
			name="Dark Chocolate",
			description="70% cocoa",
			price="4.99",
			created_by=self.admin,
			quantity_in_stock=10,
			category="chocolate",
		)

	def auth_headers(self, user):
		token = RefreshToken.for_user(user).access_token
		return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

	def test_customer_can_list_sweets(self) -> None:
		url = reverse("sweets-list")
		response = self.client.get(url, **self.auth_headers(self.customer))

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(response.data), 1)
		self.assertEqual(response.data[0]["name"], self.sample_sweet.name)

	def test_admin_can_create_sweet(self) -> None:
		url = reverse("sweets-list")
		payload = {
			"name": "Nougat Bar",
			"description": "Chewy goodness",
			"price": "2.50",
			"category": "candy",
			"quantity_in_stock": 5,
		}

		response = self.client.post(
			url, payload, format="json", **self.auth_headers(self.admin)
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertTrue(Sweet.objects.filter(name="Nougat Bar").exists())

	def test_purchase_endpoint_decrements_stock(self) -> None:
		url = reverse("sweets-purchase", args=[self.sample_sweet.pk])
		payload = {"quantity": 3}

		response = self.client.post(
			url, payload, format="json", **self.auth_headers(self.customer)
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.sample_sweet.refresh_from_db()
		self.assertEqual(self.sample_sweet.quantity_in_stock, 7)

	def test_customer_cannot_restock(self) -> None:
		url = reverse("sweets-restock", args=[self.sample_sweet.pk])
		payload = {"quantity": 5}

		response = self.client.post(
			url, payload, format="json", **self.auth_headers(self.customer)
		)

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
		self.sample_sweet.refresh_from_db()
		self.assertEqual(self.sample_sweet.quantity_in_stock, 10)

	def test_admin_can_restock(self) -> None:
		url = reverse("sweets-restock", args=[self.sample_sweet.pk])
		payload = {"quantity": 5}

		response = self.client.post(
			url, payload, format="json", **self.auth_headers(self.admin)
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.sample_sweet.refresh_from_db()
		self.assertEqual(self.sample_sweet.quantity_in_stock, 15)
