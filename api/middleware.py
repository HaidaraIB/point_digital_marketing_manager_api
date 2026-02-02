"""
Middleware to require valid X-API-Key for all /api/ requests.
"""
from django.conf import settings
from django.http import JsonResponse


class ApiKeyMiddleware:
    """
    Reject requests to /api/ that do not send a valid X-API-Key header.
    ALLOWED_API_KEYS is read from settings (comma-separated from .env).
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed_keys = set(
            k.strip()
            for k in (getattr(settings, "ALLOWED_API_KEYS", "") or "").split(",")
            if k.strip()
        )

    def __call__(self, request):
        if not request.path.startswith("/api/"):
            return self.get_response(request)

        api_key = request.headers.get("X-API-Key") or request.META.get("HTTP_X_API_KEY")
        if not api_key or api_key not in self.allowed_keys:
            return JsonResponse(
                {"detail": "Valid X-API-Key header required."},
                status=403,
            )
        return self.get_response(request)
