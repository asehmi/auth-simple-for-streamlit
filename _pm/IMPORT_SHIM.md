# Import Shim: st_auth_simple Package Wrapper

## Overview

Created a clean public API surface for the `st-auth-simple` package using a shim layer. Users now import from `st_auth_simple` instead of `authlib.auth`.

---

## Architecture

### Before
```python
from authlib.auth import auth, authenticated, requires_auth
```

### After
```python
from st_auth_simple import auth, authenticated, requires_auth
```

### How It Works

```
User Code
    │
    ├─> from st_auth_simple import ...
    │
    └─> st_auth_simple/__init__.py (shim)
        │
        └─> re-exports from authlib.auth
            │
            └─> authlib/auth.py (implementation)
            │
            └─> authlib/common/
            │
            └─> authlib/repo/
```

---

## Files Created/Modified

### New Files
- **st_auth_simple/__init__.py** — Public API shim that re-exports from `authlib.auth`

### Modified Files
- **pyproject.toml** — Added `st_auth_simple` to packages list
- **setup.py** — Updated to use `find_packages()` to auto-discover both packages
- **MANIFEST.in** — Added `st_auth_simple` files for distribution
- **app.py** — Updated imports to use `st_auth_simple`
- **admin.py** — Updated imports to use `st_auth_simple`

---

## Public API Exports

The `st_auth_simple` package exports the following:

| Function/Class | Purpose | From |
|---|---|---|
| `auth()` | Login widget wrapper | authlib.auth |
| `authenticated()` | Check if user is authenticated | authlib.auth |
| `logout()` | Logout and clear session | authlib.auth |
| `requires_auth` | Decorator for protected functions | authlib.auth |
| `admin()` | Admin mode for user management | authlib.auth |
| `override_env_storage_provider()` | Switch storage backends | authlib.auth |

---

## Usage Examples

### Basic Login
```python
import streamlit as st
from st_auth_simple import auth, authenticated

st.set_page_config(page_title="My App")

username = auth(sidebar=True)

if authenticated():
    st.write(f"Welcome, {username}!")
else:
    st.info("Please log in")
```

### Protected Functions
```python
from st_auth_simple import requires_auth

@requires_auth
def admin_panel():
    st.header("Admin Only")
    st.write("Secret content")

admin_panel()
```

### Admin Panel
```python
import streamlit as st
from st_auth_simple import admin

st.set_page_config(page_title="Auth Admin")
admin()
```

---

## Installation

### From GitHub
```bash
pip install git+https://github.com/asehmi/auth-simple-for-streamlit.git
```

### Local Development
```bash
pip install -e .
```

### Verify Installation
```bash
python -c "from st_auth_simple import auth, authenticated, requires_auth; print('SUCCESS')"
```

---

## Benefits of Shim Approach

1. **Clean Public API** — Users see `st_auth_simple`, not internal `authlib`
2. **Internal Consistency** — Keep internal structure (`authlib`) unchanged
3. **Extensibility** — Can add utility functions to the shim later without touching core
4. **Package Name Match** — `st-auth-simple` (pip) matches `st_auth_simple` (import)
5. **Semantic Clarity** — Clear distinction between public API and implementation

---

## Internal Structure (Unchanged)

The internal `authlib` package structure remains:

```
authlib/
├── auth.py              # Core authentication logic
├── common/
│   ├── crypto.py        # Encryption utilities
│   ├── cookie_manager.py
│   ├── const.py
│   └── dt_helpers.py
└── repo/
    ├── storage_factory.py
    └── provider/
        ├── sqlite/
        └── airtable/
```

Users can still import from `authlib` if needed (e.g., utilities), but the main API is `st_auth_simple`.

---

## Testing Verification

✓ `st_auth_simple` imports successfully  
✓ All 6 main exports available  
✓ `app.py` imports verified  
✓ `admin.py` imports verified  
✓ Package reinstalled with editable mode  
✓ No breaking changes to core code  

---

## Migration Guide (if upgrading from authlib imports)

### Before
```python
from authlib.auth import auth, authenticated, requires_auth
import authlib.auth as auth
```

### After
```python
from st_auth_simple import auth, authenticated, requires_auth
import st_auth_simple as auth
```

All function signatures and behavior remain identical. This is a pure import path change.

---

## Future Enhancements

The shim layer allows for future additions without modifying core:

```python
# Could add to st_auth_simple/__init__.py later:
from authlib.common import CookieManager, aes256cbcExtended
from authlib.repo.storage_factory import StorageFactory

# Utility functions specific to st_auth_simple
def setup_auth(sidebar=True, show_messages=True):
    """Convenience function for common setup"""
    pass

def is_admin():
    """Check if user is superuser"""
    pass
```

---

## Summary

The shim approach provides:
- **Cleaner imports** for users (`st_auth_simple` instead of `authlib.auth`)
- **Backward compatibility** if needed
- **Clear separation** between public API and internal implementation
- **Room for growth** without breaking internal structure

Users can now install and import like any standard Python package:
```bash
pip install st-auth-simple
```

```python
from st_auth_simple import auth, authenticated, requires_auth
```
