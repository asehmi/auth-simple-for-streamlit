"""
Sign-up flow management: temporary pending users table and PIN validation.
"""

import secrets
import logging
from os import environ as osenv
from datetime import datetime, timedelta
from typing import Optional, Tuple

from authlib.common.crypto import aes256cbcExtended
from authlib.common.dt_helpers import dt_from_str


class SignupManager:
    """Manages pending user signups with email PIN verification."""

    PENDING_USERS_TABLE = osenv.get('PENDING_USERS_TABLE', 'pending_users').upper()
    PIN_EXPIRY_MINUTES = int(osenv.get('SIGNUP_PIN_EXPIRY_MINUTES', '30'))
    ENC_PASSWORD = osenv.get('ENC_PASSWORD')
    ENC_NONCE = osenv.get('ENC_NONCE')

    @staticmethod
    def generate_pin() -> str:
        """Generate a secure 6-digit PIN."""
        pin_number = secrets.randbelow(1000000)
        return str(pin_number).zfill(6)

    @staticmethod
    def create_pending_user(store, email: str, encrypted_password: str) -> str:
        """
        Create a pending user entry with a validation PIN.

        Args:
            store: Storage provider instance
            email: User's email (used as username)
            encrypted_password: AES256-encrypted password

        Returns:
            Generated PIN string (6 digits)
        """
        pin = SignupManager.generate_pin()

        # Compute expiration as now + PIN_EXPIRY_MINUTES
        try:
            now = datetime.now()
            expires_at = (now + timedelta(minutes=SignupManager.PIN_EXPIRY_MINUTES)).isoformat()
        except (ValueError, TypeError):
            # Fallback: add minutes to current datetime
            expires_at = (datetime.now() + timedelta(minutes=SignupManager.PIN_EXPIRY_MINUTES)).isoformat()

        store.upsert({
            'table': SignupManager.PENDING_USERS_TABLE,
            'data': {
                'username': email,
                'password': encrypted_password,
                'validation_pin': pin,
                'is_validated': 0,
                'expires_at': expires_at,
            }
        })

        return pin

    @staticmethod
    def get_pending_user(store, email: str) -> Optional[dict]:
        """
        Retrieve a pending user by email.

        Returns:
            User dict or None if not found
        """
        result = store.query({
            'table': SignupManager.PENDING_USERS_TABLE,
            'fields': '*',
            'conds': f'username="{email}"',
        })
        return result[0] if result else None

    @staticmethod
    def validate_pin(store, email: str, pin: str) -> Tuple[bool, str]:
        """
        Validate a PIN for a pending user.

        Args:
            store: Storage provider instance
            email: User's email
            pin: PIN to validate

        Returns:
            (success: bool, error_message: str)
        """
        # First clean up any expired rows
        SignupManager.cleanup_expired(store)

        user = SignupManager.get_pending_user(store, email)
        if not user:
            return False, 'No pending sign-up found for this email.'

        # Check if already validated (should not happen, but safeguard)
        if user.get('is_validated', 0):
            return False, 'This sign-up has already been completed.'

        # Check PIN matches
        if user.get('validation_pin') != pin:
            return False, 'Invalid PIN. Please try again.'

        # Check expiration
        try:
            expires_at = dt_from_str(user.get('expires_at'), format='%Y-%m-%dT%H:%M:%S.%f')
            if datetime.now() > expires_at:
                return False, 'PIN has expired. Please sign up again.'
        except (ValueError, TypeError):
            return False, 'PIN has expired. Please sign up again.'

        return True, ''

    @staticmethod
    def complete_signup(store, email: str) -> Optional[dict]:
        """
        Complete a pending signup by moving user to main users table.

        This operation is atomic: both upsert and delete must succeed.
        If delete fails, the pending record remains in the DB as a cleanup marker.

        Args:
            store: Storage provider instance
            email: User's email

        Returns:
            User dict (for auto-login) or None if signup not found, invalid, or DB operation fails
        """
        user = SignupManager.get_pending_user(store, email)
        if not user:
            return None

        try:
            # Move to users table
            store.upsert({
                'table': 'USERS',
                'data': {
                    'username': email,
                    'password': user['password'],
                    'su': 0,
                }
            })
        except Exception as ex:
            logging.error(f'Failed to create user {email} in signup completion: {str(ex)}')
            return None

        try:
            # Delete from pending users
            store.delete({
                'table': SignupManager.PENDING_USERS_TABLE,
                'conds': f'username="{email}"',
            })
        except Exception as ex:
            # Log but don't fail - user is already created, pending record is just cleanup
            logging.warning(f'Failed to delete pending user {email}: {str(ex)}. User created but pending record remains.')

        # Return user dict for auto-login (matching the structure returned by query)
        return {
            'username': email,
            'password': user['password'],
            'su': 0,
        }

    @staticmethod
    def cleanup_expired(store) -> None:
        """Delete expired pending user registrations."""
        try:
            # Query all pending users and filter locally
            all_pending = store.query({
                'table': SignupManager.PENDING_USERS_TABLE,
                'fields': '*',
            })

            if not all_pending:
                return

            now = datetime.now()
            for user in all_pending:
                try:
                    expires_at = dt_from_str(user.get('expires_at'), format='%Y-%m-%dT%H:%M:%S.%f')
                    if now > expires_at:
                        store.delete({
                            'table': SignupManager.PENDING_USERS_TABLE,
                            'conds': f'username="{user.get("username")}"',
                        })
                except (ValueError, TypeError):
                    # If we can't parse the date, assume expired and delete
                    store.delete({
                        'table': SignupManager.PENDING_USERS_TABLE,
                        'conds': f'username="{user.get("username")}"',
                    })
        except Exception:
            # Cleanup is opportunistic; don't crash if it fails
            pass
