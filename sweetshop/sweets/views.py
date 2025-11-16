"""Unified DRF viewset exposing sweets CRUD, search, and inventory actions."""

from decimal import Decimal, InvalidOperation

from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Sweet
from .permissions import IsAdminUserRole
from .serializers import (
    SweetPurchaseSerializer,
    SweetRestockSerializer,
    SweetSerializer,
    SweetWriteSerializer,
)


class SweetViewSet(viewsets.ModelViewSet):
    """Single entry point for sweets with role-aware branching."""

    queryset = Sweet.objects.all().order_by("name")

    def get_serializer_class(self):
        # Mutating endpoints should use the write serializer, while
        # inventory actions rely on their dedicated payload validators.
        if self.action in {"create", "update", "partial_update"}:
            return SweetWriteSerializer
        if self.action == "purchase":
            return SweetPurchaseSerializer
        if self.action == "restock":
            return SweetRestockSerializer
        return SweetSerializer

    def get_permissions(self):
        # Customers may list/retrieve/purchase, but any admin-only
        # management actions must include the custom role permission.
        admin_actions = {"create", "update", "partial_update", "destroy", "restock"}
        permission_classes = [permissions.IsAuthenticated]
        if self.action in admin_actions:
            permission_classes.append(IsAdminUserRole)
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        # Apply filtering for query params and ensure customers only see
        # sweets that are currently in stock.
        queryset = Sweet.objects.all().order_by("name")
        request = getattr(self, "request", None)
        if request is None:
            return queryset

        category = request.query_params.get("category")
        search_term = request.query_params.get("search")

        if category:
            queryset = queryset.filter(category__iexact=category)
        if search_term:
            queryset = queryset.filter(
                Q(name__icontains=search_term) | Q(description__icontains=search_term)
            )

        if not self._is_admin(request.user):
            queryset = queryset.filter(quantity_in_stock__gt=0)

        return queryset

    def perform_create(self, serializer):
        # Persist the user who created the product for auditing.
        serializer.save(created_by=self.request.user)

    def _is_admin(self, user):
        """Small helper so multiple methods can reuse the role check."""
        return bool(user and user.is_authenticated and user.is_admin())

    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request):
        """Search sweets by name, category, or price range."""
        queryset = Sweet.objects.all().order_by("name")
        queryset = queryset if self._is_admin(request.user) else queryset.filter(quantity_in_stock__gt=0)

        name_query = request.query_params.get("name")
        category = request.query_params.get("category")
        min_price = request.query_params.get("min_price")
        max_price = request.query_params.get("max_price")

        if name_query:
            queryset = queryset.filter(
                Q(name__icontains=name_query) | Q(description__icontains=name_query)
            )
        if category:
            queryset = queryset.filter(category__iexact=category)

        try:
            if min_price:
                queryset = queryset.filter(price__gte=Decimal(min_price))
            if max_price:
                queryset = queryset.filter(price__lte=Decimal(max_price))
        except InvalidOperation:
            # Surface a helpful validation error instead of blowing up on bad decimals.
            return Response(
                {"detail": "min_price and max_price must be valid numbers."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SweetSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="purchase")
    def purchase(self, request, pk=None):
        """Allow authenticated customers to purchase sweets."""
        serializer = SweetPurchaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sweet = Sweet.objects.get(pk=pk)

        try:
            sweet.purchase(quantity=serializer.validated_data["quantity"], user=request.user)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(SweetSerializer(sweet).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="restock")
    def restock(self, request, pk=None):
        """Admin-only restock endpoint."""
        serializer = SweetRestockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sweet = Sweet.objects.get(pk=pk)

        try:
            sweet.restock(quantity=serializer.validated_data["quantity"], user=request.user)
        except PermissionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(SweetSerializer(sweet).data, status=status.HTTP_200_OK)