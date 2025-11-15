from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import Sweet


class SweetSerializer(serializers.ModelSerializer):
    """Public serializer presented in list/detail responses."""

    class Meta:
        model = Sweet
        fields = ("id", "name", "description", "price", "category", "quantity_in_stock")
        read_only_fields = fields


class SweetWriteSerializer(serializers.ModelSerializer):
    """Serializer used for create/update operations."""

    class Meta:
        model = Sweet
        fields = ("id", "name", "description", "price", "category", "quantity_in_stock")
        read_only_fields = ("id",)

    def validate_name(self, value):
        qs = Sweet.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(_("A sweet with this name already exists."))
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError(_("Price must be a positive value."))
        return value


class SweetPurchaseSerializer(serializers.Serializer):
    """Validate purchase requests."""

    quantity = serializers.IntegerField(min_value=1)

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError(_("Quantity must be a positive integer."))
        return value


class SweetRestockSerializer(serializers.Serializer):
    """Validate restock requests (admin only)."""

    quantity = serializers.IntegerField(min_value=1)

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError(_("Quantity must be a positive integer."))
        return value
