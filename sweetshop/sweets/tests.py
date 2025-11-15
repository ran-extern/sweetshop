"""TDD-first API tests for sweets CRUD and inventory actions."""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import InventoryEvent, Sweet


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
		self.candy_sweet = Sweet.objects.create(
			name="Gummy Bears",
			description="Fruity mix",
			price="1.50",
			created_by=self.admin,
			quantity_in_stock=25,
			category="candy",
		)

	def auth_headers(self, user):
		token = RefreshToken.for_user(user).access_token
		return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

	def test_customer_can_list_sweets(self) -> None:
		url = reverse("sweets-list")
		response = self.client.get(url, **self.auth_headers(self.customer))

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(response.data), 2)
		self.assertCountEqual(
			[s["name"] for s in response.data],
			[self.sample_sweet.name, self.candy_sweet.name],
		)

	def test_customer_can_view_sweet_detail(self) -> None:
		url = reverse("sweets-detail", args=[self.sample_sweet.pk])
		response = self.client.get(url, **self.auth_headers(self.customer))

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["name"], self.sample_sweet.name)
		self.assertEqual(response.data["quantity_in_stock"], self.sample_sweet.quantity_in_stock)

	def test_customer_can_filter_sweets_by_category(self) -> None:
		url = reverse("sweets-list")
		response = self.client.get(
			url + "?category=candy", **self.auth_headers(self.customer)
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(response.data), 1)
		self.assertEqual(response.data[0]["name"], self.candy_sweet.name)

	def test_customer_can_search_sweets_by_name(self) -> None:
		url = reverse("sweets-list")
		response = self.client.get(
			url + "?search=Dark", **self.auth_headers(self.customer)
		)

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
		created = Sweet.objects.get(name="Nougat Bar")
		self.assertEqual(created.created_by, self.admin)

	def test_non_admin_cannot_create_sweet(self) -> None:
		url = reverse("sweets-list")
		payload = {
			"name": "Cookie Dough",
			"description": "Raw treat",
			"price": "3.00",
			"category": "bakery",
			"quantity_in_stock": 8,
		}

		response = self.client.post(
			url, payload, format="json", **self.auth_headers(self.customer)
		)

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
		self.assertFalse(Sweet.objects.filter(name="Cookie Dough").exists())

	def test_admin_can_update_sweet(self) -> None:
		url = reverse("sweets-detail", args=[self.sample_sweet.pk])
		payload = {"price": "5.49", "description": "85% cocoa"}

		response = self.client.patch(
			url, payload, format="json", **self.auth_headers(self.admin)
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.sample_sweet.refresh_from_db()
		self.assertEqual(str(self.sample_sweet.price), "5.49")
		self.assertEqual(self.sample_sweet.description, "85% cocoa")

	def test_admin_can_delete_sweet(self) -> None:
		url = reverse("sweets-detail", args=[self.candy_sweet.pk])

		response = self.client.delete(url, **self.auth_headers(self.admin))

		self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
		self.assertFalse(Sweet.objects.filter(pk=self.candy_sweet.pk).exists())

	def test_purchase_endpoint_decrements_stock(self) -> None:
		url = reverse("sweets-purchase", args=[self.sample_sweet.pk])
		payload = {"quantity": 3}

		response = self.client.post(
			url, payload, format="json", **self.auth_headers(self.customer)
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.sample_sweet.refresh_from_db()
		self.assertEqual(self.sample_sweet.quantity_in_stock, 7)
		self.assertEqual(response.data["quantity_in_stock"], 7)

	def test_purchase_rejects_insufficient_stock(self) -> None:
		url = reverse("sweets-purchase", args=[self.sample_sweet.pk])
		payload = {"quantity": 99}

		response = self.client.post(
			url, payload, format="json", **self.auth_headers(self.customer)
		)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.sample_sweet.refresh_from_db()
		self.assertEqual(self.sample_sweet.quantity_in_stock, 10)

	def test_purchase_logs_inventory_event(self) -> None:
		url = reverse("sweets-purchase", args=[self.sample_sweet.pk])
		payload = {"quantity": 2}
		response = self.client.post(
			url, payload, format="json", **self.auth_headers(self.customer)
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		events = InventoryEvent.objects.filter(sweet=self.sample_sweet)
		self.assertTrue(events.filter(event_type=InventoryEvent.EventType.PURCHASE).exists())
		self.assertEqual(events.count(), 1)
		self.assertEqual(events.first().quantity, 2)

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
		self.assertEqual(response.data["quantity_in_stock"], 15)

	def test_restock_requires_positive_quantity(self) -> None:
		url = reverse("sweets-restock", args=[self.sample_sweet.pk])
		payload = {"quantity": 0}

		response = self.client.post(
			url, payload, format="json", **self.auth_headers(self.admin)
		)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_restock_logs_inventory_event(self) -> None:
		url = reverse("sweets-restock", args=[self.sample_sweet.pk])
		payload = {"quantity": 4}

		response = self.client.post(
			url, payload, format="json", **self.auth_headers(self.admin)
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		events = InventoryEvent.objects.filter(sweet=self.sample_sweet)
		self.assertTrue(events.filter(event_type=InventoryEvent.EventType.RESTOCK).exists())
		self.assertEqual(events.count(), 1)
		self.assertEqual(events.first().quantity, 4)
