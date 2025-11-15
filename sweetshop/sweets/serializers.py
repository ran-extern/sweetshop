from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from .models import Sweet

class SweetDetailSerializer(serializers.ModelSerializer):
    """Serializer for Sweet model."""

    class Meta:
        model = Sweet
        fields = ("id", "name", "price", "quantity_in_stock", "category", "description")
        read_only_fields = fields

class SweetCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new Sweet instances."""

    class Meta:
        model = Sweet
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at", "created_by", "id")
    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)
    def update(self, instance, validated_data):
        # Prevent updating created_by field
        validated_data.pop("created_by", None)
        validated_data["updated_at"] = serializers.DateTimeField().to_representation(serializers.datetime.now())
        return super().update(instance, validated_data)
    def validate_name(self, value):
        if Sweet.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError(_("A sweet with this name already exists."))
        return value
    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError(_("Price must be a positive value."))
        return value


class SweetPurchaseSerializer(serializers.Serializer):
    """Serializer for handling sweet purchase requests."""

    quantity = serializers.IntegerField(min_value=1)
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError(_("Quantity must be a positive integer."))
        return value
    
    

class SweetRestockSerializer(serializers.Serializer):
    """Serializer for handling sweet restock requests."""

    quantity = serializers.IntegerField(min_value=1)
    def validate(self, attrs):
        user = self.context["request"].user
        if not user.is_admin():
            raise serializers.ValidationError(
                {"detail": _("Only admin users can restock inventory.")}
            )
        return attrs
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError(_("Quantity must be a positive integer."))
        return value
    