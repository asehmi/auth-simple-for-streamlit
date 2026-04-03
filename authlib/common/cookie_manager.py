"""
CookieManager class for handling browser cookies using Streamlit's custom components.
Provides a simple interface for setting, getting, and deleting cookies.
"""

import datetime
import json
from .cookie_component import CookieComponent


class CookieManager:
    """
    Manages browser cookies using Streamlit's st.components.v2.
    Provides a simple interface for cookie operations without external dependencies.
    """

    def __init__(self):
        """Initialize the CookieManager."""
        pass

    def set(self, cookie: str, val, expires_at=None) -> None:
        """
        Set a cookie with optional expiration date.

        Args:
            cookie: Cookie name
            val: Cookie value (can be dict or string)
            expires_at: Expiration datetime (default: 30 days from now)
        """
        if expires_at is None:
            expires_at = datetime.datetime.now() + datetime.timedelta(days=30)

        # Convert dict to JSON string if needed
        cookie_value = json.dumps(val) if isinstance(val, dict) else str(val)

        CookieComponent.set_cookie(cookie, cookie_value, expires_at)

    def get(self, cookie: str):
        """
        Get a cookie value by name.

        Args:
            cookie: Cookie name

        Returns:
            Cookie value (dict if JSON, string otherwise) or None if not found
        """
        value = CookieComponent.get_cookie(cookie)
        if value:
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        return None

    def delete(self, cookie: str) -> None:
        """
        Delete a cookie by name.

        Args:
            cookie: Cookie name to delete
        """
        CookieComponent.delete_cookie(cookie)

    def get_all(self) -> dict:
        """
        Get all cookies as a dictionary.

        Returns:
            Dictionary of all cookies
        """
        return CookieComponent.get_all_cookies()
