"""
Cookie management for persistent authentication using browser cookies.
"""

import datetime
from .cookie_component import CookieComponent


class CookieManager:
    """
    Manages persistent authentication cookies.
    """

    def __init__(self):
        """Initialize the CookieManager."""
        pass

    def set(self, key: str, val, expires_at=None) -> None:
        """
        Set a cookie with optional expiration.

        Args:
            key: Cookie name
            val: Cookie value (can be dict or string)
            expires_at: Expiration datetime (default: 30 days from now)
        """
        if expires_at is None:
            expires_at = datetime.datetime.now() + datetime.timedelta(days=30)

        CookieComponent.set_cookie(key, val, expires_at)

    def get(self, cookie: str):
        """
        Get a cookie value by name.

        Args:
            cookie: Cookie name

        Returns:
            Cookie value or None if not found
        """
        return CookieComponent.get_cookie(cookie)

    def delete(self, key: str) -> None:
        """
        Delete a cookie by name.

        Args:
            key: Cookie name to delete
        """
        CookieComponent.delete_cookie(key)

    def get_all(self) -> dict:
        """
        Get all cookies (not implemented for this use case).

        Returns:
            Empty dict
        """
        return {}
