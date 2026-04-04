# Architecture: Simple Authentication for Streamlit Apps

**Version 1.0.1** | Updated April 5, 2026 | **Server-Side Session Tokens**

## Core Philosophy

This system is designed around a simple principle: **minimal, low-volume username/password authentication that integrates effortlessly into Streamlit applications**. It prioritizes ease of integration and operational simplicity over enterprise features, making it ideal for internal tools, dashboards, and small-scale applications.

The public API is accessed via the `st_auth_simple` package, providing a clean separation between the public interface and internal implementation.

---

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│              Streamlit Applications                     │
│         from st_auth_simple import (...)               │
└────────────┬────────────────────────────────────────────┘
             │
             │ Public API
             │
┌────────────▼────────────────────────────────────────────┐
│    st_auth_simple Package (Public Shim)                 │
│  Re-exports from authlib.auth for clean public API      │
└────────────┬────────────────────────────────────────────┘
             │
             │
┌────────────▼────────────────────────────────────────────┐
│         authlib.auth Module (Implementation)            │
│  ┌──────────────────────────────────────────────────┐   │
│  │  _auth()                  - Core auth logic      │   │
│  │  ├─ _try_cookie_login()   - Auto-login from     │   │
│  │  │                          persistent cookie   │   │
│  │  ├─ _show_login_form()    - Render login card   │   │
│  │  ├─ _handle_login_submit()- Validate & login    │   │
│  │  └─ _show_logged_in_ui()  - Logged-in UI        │   │
│  │                                                  │   │
│  │  auth()                   - Public wrapper       │   │
│  │  authenticated()          - Check auth state     │   │
│  │  logout()                 - Clear & rerun        │   │
│  │  requires_auth()          - Decorator            │   │
│  │  admin()                  - Admin mode           │   │
│  └──────────────────────────────────────────────────┘   │
└────┬──────────────────────┬──────────────────────────────┘
     │                      │
     │ uses                 │ uses
     │                      │
┌────▼──────────────┐  ┌────▼────────────────────────────┐
│  Session State    │  │  AuthSession                    │
│  - auth_state()   │  │  + CookieManager                │
│  - state.user     │  │  - Server-side token mgmt       │
│  - Persists       │  │  - 30-day expiration            │
│    through reruns │  │  - Stored in database           │
│                   │  │  - Synchronous validation       │
└───────────────────┘  └────┬─────────────────────────────┘
                             │
                ┌────────────┴──────────────┐
                │                           │
        ┌───────▼─────────┐    ┌───────────▼────┐
        │  Browser Cookie │    │  StorageFactory│
        │  (Token only)   │    │  - SQLite      │
        │  32-char token  │    │  - Airtable    │
        └─────────────────┘    └────┬───────────┘
                                    │
                    ┌───────────────┴────────────────┐
                    │                                │
            ┌───────▼────────┐        ┌──────────────▼──┐
            │  SQLite DB     │        │  Airtable API  │
            │  (local)       │        │  (cloud)       │
            │  users table   │        │  users table   │
            │  - username    │        │  - username    │
            │  - password*   │        │  - password*   │
            │  - su          │        │  - su          │
            │  - auth_token  │        │  - auth_token  │
            │  - expires_at  │        │  - expires_at  │
            │   *encrypted   │        │   *encrypted   │
            └────────────────┘        └────────────────┘
```

---

## Architecture Patterns

### 1. **Provider Pattern** (Storage Abstraction)
The core storage mechanism is abstracted behind a simple provider interface (`StorageProvider`). This allows multiple database backends without changing application code.

```python
# Minimal interface for flexibility
class StorageProvider(ABC):
    def query(context: dict) -> List[dict]    # READ
    def upsert(context: dict) -> None         # CREATE/UPDATE
    def delete(context: dict) -> None         # DELETE
```

**Why this pattern:**
- Easily swap between SQLite and Airtable with a single `.env` variable
- New backends (Firebase, Google Sheets, Postgres) can be added without touching core logic
- Keeps dependencies loose and testable

**Current Implementations:**
- `SQLiteProvider` — Local file-based, zero setup for development
- `AirtableProvider` — Cloud-hosted, collaborative, no database infrastructure needed

### 2. **Factory Pattern** (Provider Instantiation)
`StorageFactory` handles provider creation and caches instances using Streamlit's `@st.cache_resource` decorator.

```python
store = StorageFactory().get_provider('SQLITE' or 'AIRTABLE')
```

**Why this pattern:**
- Single point of provider instantiation
- Automatic caching prevents database reconnections on every Streamlit rerun
- Clean separation between factory logic and provider logic

### 3. **Session State Management**
Streamlit's session state is wrapped in `auth_state()` to ensure logins persist through top-to-bottom reruns.

```python
def auth_state():
    if 'user' not in state:
        state.user = None
    return state
```

**Why this pattern:**
- Streamlit reruns the entire script on every interaction; session state is the only way to maintain state
- Wrapping ensures graceful reinitialization if cache is cleared
- Decouples state management from global variables

### 4. **Decorator Pattern** (Protected Functions)
`@requires_auth` decorator protects functions so they only run when a user is authenticated.

```python
@requires_auth
def admin_function():
    # Only runs if user is authenticated
    pass
```

### 5. **Public API Shim** (Clean Exports)
The `st_auth_simple` package acts as a shim, re-exporting key functions from `authlib.auth` for a clean public API.

```python
# Users import from st_auth_simple, not authlib
from st_auth_simple import auth, authenticated, logout, requires_auth
```

This separation keeps the public interface clean while allowing internal `authlib` package to evolve without breaking the API.

### 6. **Server-Side Session Tokens** (Token Persistence)
Rather than storing user data in the browser, tokens are managed server-side:

```python
# Browser: Stores only a secure 32-character token
# Server: Stores token + expiration in database
# Read: Uses st.context.cookies to get token from browser
token = st.context.cookies.get(cookie_name)

# Write: Uses st.html() JavaScript to set browser cookie with token only
# JavaScript: document.cookie = name + "=" + token + "; expires=..."

# Validation: Token lookup in database returns user data
user = AuthSession.validate_session(store, token)
```

This provides truly persistent "Remember me" functionality while keeping the browser's token separate from sensitive user data. All validation and expiration checking happens server-side in the database.

---

## Key Components

### **authlib/auth.py** (Main API)
Entry point for all authentication functionality. Provides:

| Function | Purpose |
|----------|---------|
| `auth()` | User-facing login widget (wrapped in expander) |
| `_auth()` | Core authentication logic |
| `authenticated()` | Boolean check for current auth state |
| `logout()` | Clear session and cookies |
| `requires_auth` | Decorator to protect functions/pages |
| `admin()` | Admin mode for database initialization and user management |

### **authlib/repo/storage_factory.py** (Dependency Injection)
Instantiates the configured storage provider and caches it. Handles:
- Provider selection based on `STORAGE` env variable
- Caching via `@st.cache_resource` to prevent reconnections
- Database initialization flags (`allow_db_create`, `if_table_exists`)

### **authlib/repo/provider/** (Storage Backends)

#### Base Interface
```
provider/
├── base_provider.py         # ABC with minimal interface
├── sqlite/
│   ├── implementation.py    # SQLite implementation
│   └── settings.py          # SQLite config (DB path, name)
└── airtable/
    ├── implementation.py    # Airtable API implementation
    └── settings.py          # Airtable config (token, base, table)
```

### **authlib/common/** (Utilities)
- `crypto.py` — AES256-CBC encryption for password storage
- `cookie_manager.py` — Browser cookies for "Remember me" feature
- `const.py` — Constants (field names, message types)
- `dt_helpers.py` — Date/time utilities

### **app.py** (Demo)
Minimal example showing how to integrate `authlib` into a Streamlit app.

### **admin.py** (Admin Interface)
Streamlit app for:
- Creating/initializing the auth database
- Adding, editing, deleting users
- Designating superusers
- Only accessible in Streamlit's standalone `admin()` mode

---

## Authentication Flow

### Main Authentication Flow (`_auth()`)

```
START
  │
  ├─→ Initialize storage (once, cached)
  │
  ├─→ Show Authentication header
  │
  ├─→ Is user already authenticated in session?
  │   ├─ YES → Show logged-in UI → Return username
  │   └─ NO  → Continue
  │
  ├─→ Try auto-login from persistent cookie
  │   ├─ Cookie exists? → Validate against DB
  │       ├─ Valid? → Set session user → st.rerun() → Return username
  │       └─ Invalid? → Delete cookie → Continue
  │   └─ No cookie → Continue
  │
  └─→ Show login form (username, password, remember me)
      │
      └─ Form submitted?
         ├─ Look up user in database
         ├─ Decrypt stored password
         ├─ Compare with input
         ├─ If match:
         │  ├─ Set auth_state().user
         │  ├─ If remember me: Save cookie (30 days)
         │  └─ st.rerun()
         └─ If no match: Show error message
```

### Helper Functions (Separated for Clarity)

- **`_try_cookie_login()`** — Attempts auto-login from persistent browser cookie
  - Reads cookie via `st.context.cookies`
  - Validates password hash matches DB
  - Deletes invalid/expired cookies
  
- **`_show_login_form()`** — Renders login card with `st.form`
  - All fields visible at once (username, password, remember me)
  - Respects `sidebar` parameter for placement
  - Returns form submission data
  
- **`_handle_login_submission()`** — Validates credentials
  - Queries database for username
  - Decrypts and compares password
  - Sets session state on success
  - Saves cookie if "Remember me" checked
  
- **`_show_logged_in_ui()`** — Shows authenticated user interface
  - Displays logout button
  - Conditionally shows admin panel for superusers

### Logout Flow
1. User clicks Logout button
2. `logout()` clears session state
3. `logout()` deletes persistent cookie
4. `logout()` calls `st.rerun()` to force re-authentication
5. User sees login form again

### Server-Side Session Token Flow
1. **On Login (with Remember me):**
   - Credentials validated against database
   - `AuthSession.create_session()` generates secure 32-char token
   - Token and expiration stored in `auth_token` and `expires_at` DB columns
   - Token (only) sent to browser and stored in cookie via `st.html()` JavaScript
   - Browser sets 30-day expiration on cookie
   
2. **On Browser Reopen:**
   - Streamlit starts fresh, reruns from top
   - `st.context.cookies` immediately available
   - `_try_cookie_login()` reads 32-char token from cookie
   - `AuthSession.validate_session()` looks up token in database
   - Checks if token is expired
   - Returns user data from DB if valid, None if expired or invalid
   - User auto-logged in if valid
   
3. **On Logout:**
   - `AuthSession.clear_session()` sets `auth_token` and `expires_at` to NULL in database
   - Cookie deleted via JavaScript (or cleared on next load)
   - Session state cleared immediately
   - Next page load shows login form (token is now invalid in DB)

### Admin Flow
1. `admin()` called from `admin.py` (standalone mode)
2. Admin confirms responsibility acknowledgment
3. Database created (SQLite) or table initialized (Airtable)
4. `auth_state().user` faked with superuser status
5. Admin can manage users (create, edit, delete, list)

---

## Security Model

| Aspect | Approach | Notes |
|--------|----------|-------|
| **Passwords** | AES256-CBC encrypted | Stored encrypted in DB; never sent to browser |
| **Password Matching** | Decrypted on server, compared in-memory | Password is only in plaintext during comparison |
| **Encryption Key** | `ENC_PASSWORD` + `ENC_NONCE` from `.env` | Must be kept secret; database is useless without these |
| **Session State** | Streamlit session (in-memory) | Cleared when user closes browser/session expires |
| **Remember Me Tokens** | Server-side only | Browser stores 32-char token; user data and expiration stored in DB only |
| **Token Validation** | Database lookup on each page load | Token checked against `auth_token` column; expiration checked against `expires_at` |
| **Database Access** | Provider-specific (SQLite file perms, Airtable API token) | No built-in ACL; assumes secure deployment environment |

**Key Improvements over v1.0.0:**
- ✅ **No user data in browser** — Only a meaningless 32-char token stored in cookie
- ✅ **Server controls expiration** — Token expires in database, not just client-side
- ✅ **Synchronous logout** — Token deletion is immediate, no JavaScript timing issues
- ✅ **Better security** — Attackers gaining access to token can only see which user it belongs to, not the password

**Key Assumption:** This is for internal tools and low-volume scenarios where users are trusted and database is behind a firewall or properly secured. Not suitable for hostile environments.

---

## Configuration

### Environment Variables (`.env`)
```bash
# Required
STORAGE='SQLITE' | 'AIRTABLE'

# SQLite-specific
# (paths default to ./db/auth.db)
SQLITE_DB_PATH=./db
SQLITE_DB_NAME=auth.db

# Airtable-specific
AIRTABLE_PAT=pat_xxx               # Personal access token
AIRTABLE_BASE_KEY=app_xxx          # Base ID
USERS_TABLE=users                  # Table name

# Encryption (required)
ENC_PASSWORD=xxx                   # 32-char encryption key
ENC_NONCE=xxx                      # 16-char nonce

# Optional
COOKIE_NAME=auth_user              # Name of "Remember me" cookie
```

### Integration Example
```python
import streamlit as st
from authlib.auth import auth, authenticated, requires_auth

# Show login widget (sidebar by default)
username = auth(sidebar=True)

# Check if authenticated
if authenticated():
    st.write("Welcome!")

# Protect a section
@requires_auth
def show_admin_panel():
    st.header("Admin Only")
    # ...

show_admin_panel()
```

---

## Deployment Patterns

### Scenario 1: Local Development
```bash
STORAGE='SQLITE'
# Run admin.py to create/manage users
streamlit run admin.py

# Run main app
streamlit run app.py
```

### Scenario 2: Cloud Deployment (Streamlit Cloud)
- Use secrets manager for `.env` variables
- Choose storage: SQLite (works if app is stateless between reruns) or Airtable (recommended)
- Airtable avoids file persistence issues

### Scenario 3: Multi-User Cloud App (Airtable)
```bash
STORAGE='AIRTABLE'
# Create Airtable base + table
# Set Airtable credentials in secrets/env
# Run admin.py to initialize, add users
streamlit run app.py
```

---

## Possible Improvements

### High Priority (Within Core Philosophy)

1. **SQL Injection Prevention**
   - Currently builds queries with f-strings, e.g., `f"username=\"{username}\""`
   - **Fix:** Use parameterized queries in SQLite; use Airtable API properly (already does)
   - **Impact:** Critical security fix; low complexity

2. **Stronger Password Hashing**
   - Current: MD5 (deprecated)
   - **Upgrade:** bcrypt or argon2 for password hashing before encryption
   - **Impact:** Industry standard; small performance overhead; high security gain

3. **Audit Logging**
   - Add fields: `created_at`, `updated_at`, `last_login`, `login_count`
   - Log login attempts (success/failure) for security monitoring
   - **Impact:** Operational visibility; ~2 new DB fields

4. **Admin User List Filtering**
   - Current admin displays all users at once (scales poorly)
   - **Add:** Pagination or search in user list
   - **Impact:** Better UX for apps with many users

5. **Better Error Messages**
   - Distinguish between "user not found" and "wrong password" (currently vague)
   - Add rate-limiting hints if many failed attempts
   - **Impact:** Better UX; helps users and admins debug issues

### Medium Priority (Expanding Use Cases)

6. **Email-Based Password Reset**
   - Add password reset flow (email token, reset link)
   - **Impact:** Essential for production apps; adds email dependency

7. **Two-Factor Authentication (TOTP)**
   - Add `secret` field to store TOTP secret
   - Require time-based code on login
   - **Impact:** High security; adds complexity; ~200 LOC

8. **Role-Based Access Control (RBAC)**
   - Add `roles` field to users (e.g., "admin", "viewer", "editor")
   - Extend `@requires_auth` to accept role parameter
   - **Impact:** Multi-level access; minimal complexity

9. **OAuth2 Integration**
   - Support Google, GitHub, etc. for passwordless login
   - Keep simple: single OAuth provider per deployment
   - **Impact:** Reduces password management; adds external dependency

10. **Custom Provider Template**
    - Add boilerplate for implementing new storage providers
    - Document provider interface clearly
    - **Impact:** Helps community extend system; ~1 file to add

### Lower Priority (Philosophy Drift)

11. **User Groups / Permissions**
    - Manage groups of users with shared permissions
    - Overkill for simple apps; consider external auth solution instead

12. **Streamlit Component Wrapper**
    - Package as pip-installable component (`pip install st-auth`)
    - Reduces setup friction for new users
    - Lower priority: only useful once community adoption grows

13. **API Token Authentication**
    - Support API key/bearer token auth (non-browser clients)
    - Expands use cases but adds complexity; consider separate library

---

## Dependencies

### Core Dependencies (Required)
- **streamlit>=1.56.0** — Web framework
- **pycryptodome>=3.23.0** — AES256-CBC encryption
- **python-dotenv>=1.0.1** — Environment variable loading

### Optional Dependencies
- **pyairtable>=3.3.0** — Airtable cloud database backend (optional)

### Removed Dependencies
- ~~extra-streamlit-components~~ (v0.1.81) — Replaced with custom `st.context.cookies` + `st.html()` implementation

**Rationale for removal:** Custom cookie implementation using Streamlit's built-in APIs eliminates external dependency while providing better integration and control.

---

## Testing Strategy

Currently: Manual testing via `app.py` and `admin.py`

**Recommended Improvements:**
- Unit tests for crypto, cookie manager, provider implementations
- Integration tests for SQLite and Airtable providers
- Use pytest + fixtures for provider tests (swap between SQLite and Airtable)
- Mock Streamlit session state for unit tests
- Test cookie persistence across browser sessions
- Test logout behavior (session + cookie clearing)

---

## Known Limitations

1. **No multi-database support** — Single storage backend per deployment
2. **No user-level permissions** — All authenticated users are equal (except superusers)
3. **No rate limiting** — Vulnerable to brute-force password attacks
4. **No password policy** — Weak passwords accepted
5. **No session timeout** — Session persists until explicit logout or browser close
6. **Streamlit Cloud / Cloud Run issues** — SQLite may not persist between app restarts (use Airtable instead)
7. **JavaScript required** — Cookie functionality requires JavaScript enabled in browser (standard assumption)

---

## Summary

**st-auth-simple v1.0.1** is a production-ready authentication system excelling at its core goal: **simple, integrated username/password authentication for Streamlit apps**.

### Highlights

✅ **Pip-installable** — Standard Python package (`st-auth-simple`)  
✅ **Clean public API** — via `st_auth_simple` package shim  
✅ **Minimal dependencies** — Only Streamlit, pycryptodome, python-dotenv (core)  
✅ **Persistent login** — 30-day server-side session tokens stored in database  
✅ **Multiple backends** — SQLite (local) and Airtable (cloud)  
✅ **Clear authentication flow** — Refactored `_auth()` with logical helper functions  
✅ **Proper logout** — Synchronous DB clearing + session + forces re-authentication  
✅ **Admin interface** — User management (create, edit, delete)  
✅ **Production-ready code** — Clean, well-structured, documented  
✅ **No user data in browser** — Only 32-char tokens; validation happens server-side  

### v1.0.1 Improvements (Server-Side Tokens)

- **Token-based sessions** instead of storing user data in cookies
- **Synchronous operations** — No JavaScript timing issues on logout
- **Server-controlled expiration** — Token validity checked in database
- **Better security** — Browser never sees user credentials or encrypted passwords
- **Linear code** — No status flags needed for state management

### Architecture Strengths

- **Provider pattern** enables swapping backends without code changes
- **Session state wrapper** ensures logins survive Streamlit reruns
- **Custom cookie manager** using Streamlit native APIs (no external libs)
- **AuthSession class** manages token generation, validation, and cleanup
- **Refactored auth flow** with separation of concerns (helper functions)
- **Form-based UI** with proper login card rendering

### When to Use

Ideal for: Internal tools, dashboards, admin panels, low-threat scenarios, Streamlit Cloud deployments
Not suitable for: Public-facing apps with high security requirements, enterprise SSO

For high-security needs, consider Auth0, Firebase Auth, or enterprise solutions. For everything else, st-auth-simple delivers on its promise: **ease of integration without operational complexity**.
