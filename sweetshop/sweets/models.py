"""Inventory domain models for sweets and their stock events."""

from django.conf import settings
from django.db import models


class Category(models.TextChoices):
    """Enumerated product categories used for filtering/searching."""

    CHOCOLATE = "chocolate", "Chocolate"
    CANDY = "candy", "Candy"
    BAKERY = "bakery", "Bakery"
    GUM = "gum", "Gum"
    OTHER = "other", "Other"


class Sweet(models.Model):
    """Represents a product whose stock is tracked and sold."""

    name = models.CharField(max_length=225, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quantity_in_stock = models.PositiveIntegerField(default=0)
    category = models.CharField(
        max_length=50, choices=Category.choices, default=Category.OTHER
    )

    def __str__(self) -> str:
        return self.name

    def purchase(self, quantity: int, user=None) -> None:
        """Decrease stock for a customer purchase and create an audit log."""

        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        if quantity > self.quantity_in_stock:
            raise ValueError("Insufficient stock for the requested purchase.")

        self.quantity_in_stock -= quantity
        InventoryEvent.objects.create(
            sweet=self,
            event_type=InventoryEvent.EventType.PURCHASE,
            quantity=quantity,
            performed_by=user,
        )
        self.save(update_fields=["quantity_in_stock", "updated_at"])

    def restock(self, quantity: int, user=None) -> None:
        """Allow admins to add stock while logging who performed the action."""

        if user is None or not user.is_admin():
            raise PermissionError("Only admin users can restock inventory.")
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")

        self.quantity_in_stock += quantity
        InventoryEvent.objects.create(
            sweet=self,
            event_type=InventoryEvent.EventType.RESTOCK,
            quantity=quantity,
            performed_by=user,
        )
        self.save(update_fields=["quantity_in_stock", "updated_at"])


class InventoryEvent(models.Model):
    """Immutable ledger capturing every inventory-changing action."""

    class EventType(models.TextChoices):
        """Categorizes whether an event represents a purchase or restock."""
        PURCHASE = "purchase", "Purchase"
        RESTOCK = "restock", "Restock"

    sweet = models.ForeignKey(
        Sweet,
        related_name="inventory_events",
        on_delete=models.CASCADE,
    )
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    quantity = models.PositiveIntegerField()
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inventory_events",
    )
    occurred_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-occurred_at"]

    def __str__(self):
        return f"{self.get_event_type_display()} {self.quantity} of {self.sweet.name}"