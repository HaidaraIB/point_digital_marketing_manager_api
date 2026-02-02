"""
Custom permissions for Point Digital Marketing Manager API.
"""
from rest_framework import permissions


class IsAuthenticatedReadOnlyOrAdmin(permissions.BasePermission):
    """
    Allow read-only for any authenticated user; allow write (create/update/delete)
    only for users with role ADMIN.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return getattr(request.user, "role", None) == "ADMIN"


class IsAdminUser(permissions.BasePermission):
    """Allow access only to users with role ADMIN."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == "ADMIN"
        )
