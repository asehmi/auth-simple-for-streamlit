"""
st-auth-simple: Simple authentication for Streamlit apps

A lightweight, pluggable authentication library for Streamlit applications
supporting multiple storage backends (SQLite, Airtable).

Example:
    >>> import streamlit as st
    >>> from st_auth_simple import auth, authenticated, requires_auth
    >>>
    >>> st.set_page_config(page_title="My App")
    >>> username = auth(sidebar=True)
    >>>
    >>> if authenticated():
    ...     st.write(f"Welcome, {username}!")
    >>> else:
    ...     st.info("Please log in to continue")
    >>>
    >>> @requires_auth
    ... def admin_panel():
    ...     st.header("Admin Only")
    ...
    >>> admin_panel()
"""

from authlib.auth import (
    auth,
    authenticated,
    logout,
    requires_auth,
    admin,
    override_env_storage_provider,
)

__version__ = "1.0.0"
__author__ = "Arvindra Sehmi"
__license__ = "MIT"

__all__ = [
    "auth",
    "authenticated",
    "logout",
    "requires_auth",
    "admin",
    "override_env_storage_provider",
]
