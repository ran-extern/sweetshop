"""APIView-based boilerplate for sweets, split between customer/admin use."""

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .permissions import IsAdminUserRole
from .models import Sweet
from .serializers import (
    SweetPurchaseSerializer,
    SweetRestockSerializer,
    SweetDetailSerializer,
    SweetCreateSerializer,
)


class CustomerSweetListView(APIView):
    """Expose read-only catalog data to authenticated customers."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Return the sweets collection with optional filtering."""
        queryset = Sweet.objects.all()
        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(name__icontains=search)
        category = request.query_params.get("category")
        if category:
            queryset =queryset.filter(category__iexact=category)
        serializer = SweetDetailSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CustomerSweetDetailView(APIView):
    """Expose an individual sweet to customers."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        """Return a single sweet entry."""
        queryset = Sweet.objects.filter(pk=pk)
        if not queryset.exists():
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        sweet =queryset.first()
        serializer = SweetDetailSerializer(sweet)
        return Response(serializer.data, status=status.HTTP_200_OK)
        


class CustomerPurchaseView(APIView):
    """Allow customers to purchase a sweet and decrease inventory."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        """Process a purchase quantity for the specified sweet."""
        queryset = Sweet.objects.filter(pk=pk)
        if not queryset.exists():
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        sweet =queryset.first()
        serializer = SweetPurchaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quantity = serializer.validated_data["quantity"]
        if sweet.quantity_in_stock < quantity:
            return Response(
                {"detail": "Insufficient stock for the requested quantity."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        sweet.purchase(quantity, user=request.user)
        return Response(SweetDetailSerializer(sweet).data, status=status.HTTP_200_OK)


class AdminSweetListCreateView(APIView):
    """Admin-only listing and creation endpoint."""

    permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]
    def get(self, request):
        """Return the sweets collection for admin oversight."""
        queryset = Sweet.objects.all()
        serializer = SweetDetailSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new sweet record on behalf of an admin."""
        serializer=SweetCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        sweet = serializer.save()
        return Response(SweetDetailSerializer(sweet).data, status=status.HTTP_201_CREATED)


class AdminSweetDetailView(APIView):
    """Admin-only detail endpoint supporting updates/deletes."""

    permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]

    def get(self, request, pk):
        """Return a single sweet for admin management."""
        queryset = Sweet.objects.filter(pk=pk)
        if not queryset.exists():
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        sweet = queryset.first()
        serializer = SweetDetailSerializer(sweet)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        """Partially update a sweet's attributes."""
        queryset = Sweet.objects.filter(pk=pk)
        if not queryset.exists():
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        sweet = queryset.first()
        serializer = SweetCreateSerializer(
            sweet, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        updated_sweet = serializer.save()
        return Response(SweetDetailSerializer(updated_sweet).data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        """Remove a sweet from the catalog."""
        queryset = Sweet.objects.filter(pk=pk)
        if not queryset.exists():
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        sweet = queryset.first()
        sweet.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminRestockView(APIView):
    """Admin-only endpoint to restock inventory for a sweet."""

    permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]

    def post(self, request, pk):
        """Increase inventory and log the restock event."""
        queryset = Sweet.objects.filter(pk=pk)
        if not queryset.exists():
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        sweet =queryset.first()
        serializer = SweetRestockSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        quantity = serializer.validated_data["quantity"]
        sweet.restock(quantity, user=request.user)
        return Response(SweetDetailSerializer(sweet).data, status=status.HTTP_200_OK)