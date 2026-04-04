"""
Cookie management using Streamlit's st.context.cookies and st.html()
Provides browser cookie handling with read/write access.
"""

import datetime
import json
import streamlit as st


class CookieComponent:
    """Manages cookies using Streamlit's st.context.cookies and st.html()."""

    @staticmethod
    def get_cookie(name: str):
        """Get a cookie value from the browser using st.context.cookies."""
        try:
            cookies = st.context.cookies
            if not cookies or name not in cookies:
                return None

            value = cookies[name]
            if not value:
                return None

            # Value might be URL-encoded, so decode it
            from urllib.parse import unquote
            decoded_value = unquote(value)

            # Try to parse as JSON (for dict values)
            try:
                return json.loads(decoded_value)
            except (json.JSONDecodeError, TypeError, ValueError):
                # Return as string if not JSON
                return decoded_value
        except Exception:
            pass
        return None

    @staticmethod
    def set_cookie(name: str, value: str, expires_at=None) -> None:
        """Set a cookie in the browser using st.html() JavaScript injection."""
        if expires_at is None:
            expires_at = datetime.datetime.now() + datetime.timedelta(days=30)

        expires_str = expires_at.isoformat() if expires_at else "null"

        # Inject JavaScript to set the cookie
        cookie_script = f"""
        <script>
            (function() {{
                const value = {json.dumps(value)};
                const expiresAt = {json.dumps(expires_str)};
                let expires = "";
                if (expiresAt) {{
                    expires = "; expires=" + new Date(expiresAt).toUTCString();
                }}
                document.cookie = {json.dumps(name)} + "=" + encodeURIComponent(typeof value === 'string' ? value : JSON.stringify(value)) + expires + "; path=/; SameSite=Lax";
            }})();
        </script>
        """
        st.html(cookie_script, unsafe_allow_javascript=True)

    @staticmethod
    def delete_cookie(name: str) -> None:
        """Delete a cookie from the browser using st.html() JavaScript injection."""
        cookie_script = f"""
        <script>
            document.cookie = {json.dumps(name)} + "=; expires=" + new Date(0).toUTCString() + "; path=/; SameSite=Lax";
        </script>
        """
        st.html(cookie_script, unsafe_allow_javascript=True)
