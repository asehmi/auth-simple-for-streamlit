"""
Session token management for persistent authentication using browser storage.
"""

import datetime
from .session_token_component import SessionTokenComponent


class SessionTokenManager:
    """
    Manages persistent session tokens.
    """

    def __init__(self):
        """Initialize the SessionTokenManager."""
        pass

    def set(self, key: str, val, expires_at=None) -> None:
        """
        Persist a session token with optional expiration.

        Args:
            key: Token name
            val: Token value (can be dict or string)
            expires_at: Expiration datetime (default: 30 days from now)
        """
        if expires_at is None:
            expires_at = datetime.datetime.now() + datetime.timedelta(days=30)

        SessionTokenComponent.persist_token(key, val, expires_at)

    def get(self, token: str):
        """
        Retrieve a session token by name.

        Args:
            token: Token name

        Returns:
            Token value or None if not found
        """
        return SessionTokenComponent.retrieve_token(token)

    def delete(self, key: str) -> None:
        """
        Clear a session token by name.

        Args:
            key: Token name to clear
        """
        SessionTokenComponent.clear_token(key)

    def get_all(self) -> dict:
        """
        Get all tokens (not implemented for this use case).

        Returns:
            Empty dict
        """
        return {}
