# Installing st-auth-simple as a Package

## Overview

`st-auth-simple` is now a pip-installable package, making it easy to integrate simple authentication into any Streamlit project without copying files around.

---

## Installation Methods

### 1. From GitHub (Recommended for Development)

```bash
# Latest development version
pip install git+https://github.com/asehmi/auth-simple-for-streamlit.git

# With Airtable support
pip install git+https://github.com/asehmi/auth-simple-for-streamlit.git#egg=st-auth-simple[airtable]
```

### 2. From Local Directory

When working locally on the package:

```bash
# Install in development mode (editable install)
cd /path/to/auth-simple-for-streamlit
pip install -e .

# With Airtable support
pip install -e ".[airtable]"

# With development tools (testing, linting)
pip install -e ".[dev]"

# With everything
pip install -e ".[all]"
```

### 3. From PyPI (Future)

Once published to PyPI:

```bash
pip install st-auth-simple

# With Airtable support
pip install st-auth-simple[airtable]
```

---

## Package Structure

```
st-auth-simple/
├── authlib/
│   ├── __init__.py          # Main exports
│   ├── auth.py              # Core auth module
│   ├── common/              # Utilities (crypto, cookies, etc.)
│   │   ├── __init__.py
│   │   ├── const.py
│   │   ├── crypto.py
│   │   ├── cookie_manager.py
│   │   └── dt_helpers.py
│   └── repo/                # Storage providers
│       ├── __init__.py
│       ├── storage_factory.py
│       └── provider/
│           ├── base_provider.py
│           ├── sqlite/
│           │   ├── implementation.py
│           │   ├── settings.py
│           │   └── __init__.py
│           └── airtable/
│               ├── implementation.py
│               ├── settings.py
│               └── __init__.py
├── pyproject.toml           # Modern Python packaging config
├── setup.py                 # Legacy setup script
├── setup.cfg                # Additional config
├── MANIFEST.in              # Non-Python file inclusion
├── README.md                # Project readme
└── LICENSE                  # MIT License
```

---

## Using the Package in Your Project

### Basic Setup

1. **Install the package:**

   ```bash
   pip install git+https://github.com/asehmi/auth-simple-for-streamlit.git
   ```

2. **Create `.env` file in your project:**

   ```bash
   # Storage backend (SQLITE or AIRTABLE)
   STORAGE='SQLITE'

   # Encryption settings (required)
   ENC_PASSWORD='your-32-char-key-here'
   ENC_NONCE='your-16-char-key'

   # Optional: Cookie settings
   COOKIE_NAME='auth_user'

   # SQLite (optional, defaults shown)
   SQLITE_DB_PATH='./db'
   SQLITE_DB_NAME='auth.db'

   # OR Airtable (if using Airtable)
   AIRTABLE_PAT='pat_xxx'
   AIRTABLE_BASE_KEY='app_xxx'
   USERS_TABLE='users'
   ```

3. **Create `admin.py` to manage users:**

   ```python
   import streamlit as st
   from authlib.auth import admin

   st.set_page_config(page_title="Auth Admin")
   admin()
   ```

4. **Create your main app (`app.py`):**

   ```python
   import streamlit as st
   from authlib.auth import auth, authenticated, requires_auth

   st.set_page_config(page_title="My App")

   # Show login widget
   username = auth(sidebar=True)

   if authenticated():
       st.title("Welcome!")
       st.write(f"Logged in as: {username}")
   else:
       st.info("Please log in to continue")

   # Protected function example
   @requires_auth
   def admin_panel():
       st.header("Admin Only Section")
       st.write("Secret admin content here")

   admin_panel()
   ```

### Import Patterns

```python
# Import authentication functions
from authlib.auth import (
    auth,              # Login widget
    authenticated,     # Check auth status
    logout,            # Logout
    requires_auth,     # Decorator
)

# Import utilities
from authlib.common import (
    aes256cbcExtended,  # Encryption
    CookieManager,      # Cookie handling
    const,              # Constants
)

# Import storage
from authlib.repo.storage_factory import StorageFactory
```

---

## Development Workflow

### Setting Up for Local Development

```bash
# Clone the repo
git clone https://github.com/asehmi/auth-simple-for-streamlit.git
cd auth-simple-for-streamlit

# Install in editable mode with dev dependencies
pip install -e ".[dev,airtable]"

# Run tests
pytest

# Run linting
flake8 authlib/
black authlib/
mypy authlib/
```

### Building the Package

```bash
# Install build tools
pip install build twine

# Build distribution
python -m build

# This creates:
# - dist/st-auth-simple-1.0.0.tar.gz (source distribution)
# - dist/st-auth-simple-1.0.0-py3-none-any.whl (wheel)

# Test locally
pip install dist/st-auth-simple-1.0.0-py3-none-any.whl
```

---

## Version Management

The package uses semantic versioning:

- **Major (1.x.0)** — Breaking changes
- **Minor (1.0.x)** — New features, backwards compatible
- **Patch (1.0.0)** — Bug fixes

Update version in:
- `pyproject.toml` (primary)
- `setup.py` (legacy, should match pyproject.toml)
- `setup.cfg` (optional)

---

## Dependencies

### Core Dependencies
- `streamlit>=1.35.0` — Web framework
- `pycryptodome==3.18.1` — Encryption
- `extra-streamlit-components==0.1.71` — Cookie manager

### Optional Dependencies
- `pyairtable==2.3.1` — Airtable backend (install with `[airtable]` extra)

### Development Dependencies
- `pytest` — Testing
- `black` — Code formatting
- `flake8` — Linting
- `mypy` — Type checking

---

## Common Issues

### Issue: "Module authlib not found"
**Solution:** Make sure you installed the package:
```bash
pip install git+https://github.com/asehmi/auth-simple-for-streamlit.git
```

### Issue: "Auth DB Not Found" error
**Solution:** Run `admin.py` in standalone mode to initialize the database:
```bash
streamlit run admin.py
```

### Issue: "Encryption key not found"
**Solution:** Ensure `.env` file has `ENC_PASSWORD` and `ENC_NONCE`:
```bash
# Generate random keys
python -c "import os; print(os.urandom(32).hex())"  # 32-char password
python -c "import os; print(os.urandom(16).hex())"  # 16-char nonce
```

### Issue: Airtable connection fails
**Solution:** Check Airtable credentials in `.env`:
```bash
# Verify these exist and are correct
AIRTABLE_PAT='pat_...'
AIRTABLE_BASE_KEY='app_...'
USERS_TABLE='users'
```

---

## Publishing to PyPI

When ready to publish publicly:

```bash
# Build the package
python -m build

# Upload to PyPI (requires account)
twine upload dist/st-auth-simple-1.0.0*

# For test PyPI first:
twine upload --repository testpypi dist/st-auth-simple-1.0.0*
```

Then users can simply run:
```bash
pip install st-auth-simple
```

---

## Next Steps

1. **Test the installation** in a fresh environment
2. **Add CI/CD pipeline** (GitHub Actions) to run tests on push
3. **Publish to PyPI** once confident in API stability
4. **Create tutorial/example projects** showing usage patterns
5. **Gather community feedback** on API and features
