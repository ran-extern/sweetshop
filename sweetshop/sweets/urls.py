from django.urls import path

from .views import (
    AdminRestockView,
    AdminSweetDetailView,
    AdminSweetListCreateView,
    CustomerPurchaseView,
    CustomerSweetDetailView,
    CustomerSweetListView,
)


urlpatterns = [
    # Customer-facing endpoints
    path("sweets/", CustomerSweetListView.as_view(), name="sweets-list"),
    path("sweets/<int:pk>/", CustomerSweetDetailView.as_view(), name="sweets-detail"),
    path("sweets/<int:pk>/purchase/", CustomerPurchaseView.as_view(), name="sweets-purchase"),

    # Admin-only endpoints
    path("admin/sweets/", AdminSweetListCreateView.as_view(), name="admin-sweets-list"),
    path("admin/sweets/<int:pk>/", AdminSweetDetailView.as_view(), name="admin-sweets-detail"),
    path("admin/sweets/<int:pk>/restock/", AdminRestockView.as_view(), name="sweets-restock"),
]
