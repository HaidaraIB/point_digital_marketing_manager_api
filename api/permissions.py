"""
Custom permissions for Point Digital Marketing Manager API.
"""
from rest_framework import permissions


def _is_admin(user):
    return getattr(user, "role", None) == "ADMIN"


def _is_accountant(user):
    return getattr(user, "role", None) == "ACCOUNTANT"


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
        return _is_admin(request.user)


class IsAdminUser(permissions.BasePermission):
    """Allow access only to users with role ADMIN."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and _is_admin(request.user)
        )


class IsAccountantReadAddOrAdmin(permissions.BasePermission):
    """
    For ACCOUNTANT: allow GET (read) and POST (add) only; no PUT/PATCH/DELETE.
    For ADMIN: allow all methods.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if _is_admin(request.user):
            return True
        if _is_accountant(request.user):
            return request.method in ("GET", "HEAD", "OPTIONS", "POST")
        return False
