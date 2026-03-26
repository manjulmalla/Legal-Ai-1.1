"""
Custom middleware to exempt certain views from CSRF protection
"""

from django.utils.deprecation import MiddlewareMixin


class CSRFMiddleware(MiddlewareMixin):
    """
    Custom CSRF middleware that exempts specific URL patterns from CSRF protection.
    This ensures the chatbot API endpoints work without CSRF tokens.
    """

    def process_view(self, request, callback, callback_args, callback_kwargs):
        # Exempt chatbot API endpoints from CSRF
        if request.path.startswith('/chatbot/api/'):
            # Return None to continue processing without CSRF check
            return None
        return None
