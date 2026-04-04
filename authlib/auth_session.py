"""
Server-side session management using database auth tokens.
No browser cookies, no JavaScript complexity - just clean DB-stored tokens.
"""

import secrets
import datetime
from . import const


class AuthSession:
    """Manages persistent authentication via server-side tokens stored in DB."""

    @staticmethod
    def generate_token() -> str:
        """Generate a secure random token."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def create_session(store, user: dict, expires_in_days: int = 30) -> str:
        """
        Create a persistent session for a user.

        Args:
            store: Storage provider (SQLite or Airtable)
            user: User dict from database
            expires_in_days: Token expiration in days

        Returns:
            Auth token string
        """
        token = AuthSession.generate_token()
        expires_at = (datetime.datetime.now() + datetime.timedelta(days=expires_in_days)).isoformat()

        # Update user record with token in DB
        ctx = {
            'data': {
                const.USERNAME: user[const.USERNAME],
                const.PASSWORD: user[const.PASSWORD],
                const.SU: user[const.SU],
                const.AUTH_TOKEN: token,
                const.EXPIRES_AT: expires_at,
            }
        }
        store.upsert(context=ctx)

        return token

    @staticmethod
    def validate_session(store, token: str):
        """
        Validate a session token and return the user if valid.

        Args:
            store: Storage provider
            token: Auth token to validate

        Returns:
            User dict if valid, None if invalid/expired
        """
        if not token:
            return None

        # Query for user with this token
        ctx = {'fields': "*", 'conds': f"{const.AUTH_TOKEN}=\"{token}\""}
        data = store.query(context=ctx)

        if not data:
            return None

        user = data[0]

        # Check if token has expired
        if const.EXPIRES_AT in user and user[const.EXPIRES_AT]:
            try:
                expires_at = datetime.datetime.fromisoformat(user[const.EXPIRES_AT])
                if datetime.datetime.now() > expires_at:
                    # Token expired, clear it
                    AuthSession.clear_session(store, user[const.USERNAME])
                    return None
            except (ValueError, TypeError):
                pass

        return user

    @staticmethod
    def clear_session(store, username: str) -> None:
        """
        Clear the session token for a user (on logout).

        Args:
            store: Storage provider
            username: Username to clear token for
        """
        # Query for user to get their data
        ctx = {'fields': "*", 'conds': f"{const.USERNAME}=\"{username}\""}
        data = store.query(context=ctx)

        if data:
            user = data[0]
            # Update user record, clearing the token
            ctx = {
                'data': {
                    const.USERNAME: user[const.USERNAME],
                    const.PASSWORD: user[const.PASSWORD],
                    const.SU: user[const.SU],
                    const.AUTH_TOKEN: None,
                    const.EXPIRES_AT: None,
                }
            }
            store.upsert(context=ctx)
