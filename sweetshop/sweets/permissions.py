from rest_framework.permissions import BasePermission
"""Admin permissions for sweets app."""
class IsAdminUserRole(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin())