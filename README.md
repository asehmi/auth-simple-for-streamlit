
# Simple Authentication for Streamlit Apps
> _A simple username/password database authentication solution for Streamlit with server-side session tokens_

> Arvindra Sehmi, CloudOpti Ltd. | [Website](https://sehmi-conscious.medium.com/about) | [LinkedIn](https://www.linkedin.com/in/asehmi/)

> **Version 1.0.2** | Updated: April 5, 2026

---

**TL;DR:** A simple, production-ready username/password authentication solution with:
- Server-side session tokens (no sensitive data in browser)
- Optional email-based user signup with PIN verification
- Support for SQLite (local) and Airtable (cloud) backends
- Pluggable message callbacks for custom UI integration
- Persistent "Remember me" sessions (30 days)

## Quick start

To get started immediately with a SQLite database, follow these steps:

1. Clone this repo
2. Copy the sample environment settings file `.env.sample` to `.env`
3. Install requirements

    > `pip install -r requirements.txt`

4. *(Optional)* Configure SendGrid for email signup:
   - Get an API key from [SendGrid](https://sendgrid.com)
   - Add to `.env`: `SENDGRID_API_KEY=...` and `NOTIFICATION_FROM_EMAIL=...`
   - Set `ALLOW_USER_SIGN_UP='True'` in `.env` to enable self-service signup

5. Initialize the SQLite database and create some users (including at least one super user)

    > `streamlit run admin.py`

6. Finally, run the test application

    > `streamlit run app.py`

## Introduction

This is **not** an identity solution, it's a simple username/password login authentication solution using a backing database inspired by [this post](https://discuss.streamlit.io/t/authentication-script/14111) (written by [madflier](https://discuss.streamlit.io/u/madflier)) over in the [Streamlit discussion forum](https://discuss.streamlit.io/).

I've previously implemented an authentication and identity solution: [Streamlit component for Auth0 Authentication](https://github.com/asehmi/Data-Science-Meetup-Oxford/tree/master/StreamlitComponent). That's definitely the solution I'd recommend but feel that the Streamlit community has been slow to take it up. Perhaps it's considered to be something for _big enterprise_ applications? Given how easy it is to use [Auth0](https://auth0.com) that's not true. Or perhaps, because Streamlit components can get complicated and require separate Streamlit and web apps to make them work, something else with fewer moving parts is more desirable? I don't know for sure what the blockers are and will be producing some tutorials on Auth0 + Streamlit integration soon to help educate our community.

In the meantime, I think a solution like madflier's will be more palatable for many folks getting started with Streamlit **and** needing authentication? To fill this gap, I thought I'd build on his application and improve its _flexibility_ and _production readiness_. Though my aim is contrary to madflier's objectives around simplicity, there are so many requests for simple database-backed authentication in the Streamlit discussion forum that I felt it was worth the effort to take his solution several steps further. As an honorary member of Streamlit's [Creators](https://streamlit.io/creators) group I recently had the opportunity to work on my idea in a Streamlit-internal hackathon and this is what I'll describe here. Allow me to both apologise to madflier for the many changes I've made to his design and thank him for the initial spark! :-)

## What I've built

**v1.0.2 Highlights:**

- **Server-side session tokens** — Browser stores only a 32-character meaningless token; all user data stays on the server. Token metadata (expiration) validated on every page load. Provides strong security by design.

- **Session state support** — Logins survive Streamlit's top-down reruns via isolated `st.session_state['auth_state']` dictionary, preventing collision with client app state.

- **Email-based signup with PIN verification** — Optional self-service user registration via SendGrid email with 6-digit PIN validation. Users move from `PENDING_USERS` → `USERS` table after PIN verification.

- **Pluggable message callbacks** — Client apps control how auth messages are displayed via `on_message_cb` parameter. Supports custom callbacks, console output, or silent mode. Decouples message presentation from library logic.

- **Logout is immediate** — Server-side token clearance makes logout synchronous (no JavaScript race conditions or timing issues).

- **Support for `logout`, `authenticated` check, and `requires_auth` decorator** to protect areas of your own apps (e.g., secure pages in multi-page Streamlit apps).

- **Built-in authentication UI** — Login/signup forms and status header that integrate seamlessly into Streamlit apps.

- **Provider design pattern** — Database abstraction layer allows swapping between SQLite and Airtable with a single `.env` variable.

- **Multiple backends** — [Airtable](https://airtable.com) cloud database provider alongside local SQLite. Abstract interface allows easy addition of Firebase, Google Sheets, Postgres, etc.

- **Strong password security** — Passwords encrypted with AES256-CBC and never sent to browser. Decryption and validation happen server-side only.

- **Externalized configuration** — All secrets and settings managed via `.env` file (tokens, API keys, database paths, table names, encryption keys, etc.).

- **Robust error handling** — Failsafe DB write operations prevent inconsistent state. All errors logged appropriately.

- **Production-ready code** — Well-structured, fully documented, pip-installable package.

## Key Features by Version

**v1.0.0** — Initial release with SQLite/Airtable support and basic session management.

**v1.0.1** — Refactored to server-side session tokens, added "Remember me" persistence, improved security model.

**v1.0.2 (Current)** — Email signup with PIN verification, pluggable message callbacks, session state isolation, terminology cleanup (cookies → session tokens).

## Contributions

- Session token architecture and design principles
- Email signup with PIN verification via SendGrid
- Message callback pattern for decoupled UI
- Improved error handling and state management
- Contributions welcome! See [LICENSE](./LICENSE) (MIT)


All code is published under [MIT license](./LICENSE), so feel free to make changes and please **fork the repo if you're making changes and submit pull requests**.

If you like this work, consider clicking that **star** button. Thanks!

## Demos

### Test application

The Streamlit app `app.py` illustrates how to hook `authlib` into your Streamlit applications.

![app.py](./auth-simple-demo.gif)

### Database Admin

The Streamlit app `admin.py` illustrates how to auto-start `authlib`'s superuser mode to create an initial SQLite database and manage users and user credentials.

![admin.py](./auth-simple-admin-demo.gif)

## Installation and running the app

### Option 1: Run the demo locally (development)

To install the pre-requisites and run the demo apps:

```bash
$ pip install -r requirements.txt
$ streamlit run app.py
```

To initialize the database, run the admin app:

```bash
$ streamlit run admin.py
```

### Option 2: Install as a library in your own apps

To use `st-auth-simple` in your local Streamlit applications, install it in development mode:

```bash
# From the root of this repository
$ pip install -e .
```

This installs the `st_auth_simple` package in editable mode, allowing you to:
- Import from your apps: `from st_auth_simple import auth, authenticated, logout, requires_auth`
- Make changes to the library and see them reflected immediately (no reinstall needed)
- Keep a single copy of the library while developing multiple apps

**To include optional Airtable support:**

```bash
$ pip install -e ".[airtable]"
```

**In your Streamlit app:**

```python
from st_auth_simple import auth, authenticated, requires_auth
from authlib.common import const

def my_message_handler(msg: str, type: int):
    if type == const.ERROR:
        st.error(msg)
    # ... handle other message types
    
# Call auth() with your custom callback
user = auth(sidebar=True, on_message_cb=my_message_handler)

if authenticated():
    st.success(f"Welcome, {user}!")
else:
    st.info("Please log in to continue")
```

**Using the decorator to protect functions:**

```python
@requires_auth
def admin_panel():
    st.subheader("Admin Controls")
    # This only runs if user is authenticated
    pass
```

### Running the demo apps with library changes

If you're developing changes to the library and want to test with the demo apps:

```bash
# Install library in editable mode
$ pip install -e .

# Run the demo
$ streamlit run app.py
```

Any changes to `authlib/` will be reflected on the next page reload (Streamlit rerun).

## Getting started with a SQLite database

There's nothing you need to do as SQLite is part of Python (I use version 3.8.10). The `admin.py` Streamlit application will handle creating a database and `users` table for you, and then allow you to populate users, and edit existing databases.

1. First, assign the `STORAGE` value in the `.env` file in the application root folder.

For example:

**.env** file

```bash
# Options are 'SQLITE', 'AIRTABLE'
STORAGE='SQLITE'
```

A full example (which includes Airtable and encryption key settings) is available in `env.sample`.

2. Then, you must run the admin app as shown above to create your initial SQLite database!

## Getting started with an Airtable database

### How to create an Airtable

1. Login to or create a (free) [**Airtable account**](https://airtable.com/account)
2. Create a base (database) and add the required tables:

**users table:**
| Field | Type | Notes |
|-------|------|-------|
| `username` | Single line text | Primary key; stores email |
| `password` | Single line text | AES256-CBC encrypted |
| `su` | Number | 0 or 1 (superuser flag) |
| `auth_token` | Single line text | Session token (empty if not logged in) |
| `expires_at` | Single line text | ISO format datetime |

**PENDING_USERS table:** *(Only if `ALLOW_USER_SIGN_UP='True'`)*
| Field | Type | Notes |
|-------|------|-------|
| `username` | Single line text | Email awaiting verification |
| `password` | Single line text | AES256-CBC encrypted |
| `validation_pin` | Single line text | 6-digit PIN |
| `is_validated` | Number | 0 (pending) or 1 (verified) |
| `expires_at` | Single line text | PIN expiry time (ISO format) |

### Finding your Airtable settings

1. Create a Personal Access Token in [Developer Hub](https://airtable.com/create/tokens)
2. For your base, go to Help → API documentation → METADATA
3. In the curl example, extract:
   - `YOUR_SECRET_API_TOKEN` → Your `AIRTABLE_PAT`
   - `appv---X---c` → Your `AIRTABLE_BASE_KEY`
   - Table names → `USERS_TABLE` and `PENDING_USERS_TABLE`

Example:
```bash
$ curl https://api.airtable.com/v0/appv---X---c/users -H "Authorization: Bearer YOUR_SECRET_API_TOKEN"
```

### Configuring Airtable in .env

**.env** file
```bash
STORAGE='AIRTABLE'
AIRTABLE_PAT='pat---X---e'
AIRTABLE_BASE_KEY='app---X---c'
USERS_TABLE='users'
PENDING_USERS_TABLE='PENDING_USERS'
```

See `.env.sample` for a complete example.

## Configuring Email Signup (SendGrid)

To enable self-service user signup with email verification:

1. Create a [SendGrid](https://sendgrid.com) account and generate an API key
2. Add to `.env`:
```bash
ALLOW_USER_SIGN_UP='True'
SENDGRID_API_KEY='SG.xxxxx...'
NOTIFICATION_FROM_EMAIL='noreply@yourapp.com'
SIGNUP_PIN_EXPIRY_MINUTES='30'  # Optional, defaults to 30
PENDING_USERS_TABLE='PENDING_USERS'  # Required
```

3. Create the `PENDING_USERS` table in Airtable or SQLite (SQLite is auto-created)

When enabled, users will see a "Sign Up" tab alongside the Login form. They'll enter email + password, receive a 6-digit PIN via email, verify it, and automatically be logged in.

## Using the Auth Callback Pattern

Client apps can control how auth messages are displayed by passing a callback function:

```python
from authlib.common import const
import streamlit as st

def my_message_handler(msg: str, type: int):
    """Custom message display using Streamlit widgets."""
    if type == const.ERROR:
        st.error(msg)
    elif type == const.SUCCESS:
        st.success(msg)
    elif type == const.WARNING:
        st.warning(msg)
    else:
        st.info(msg)

# Pass callback to auth()
user = auth(sidebar=True, on_message_cb=my_message_handler)

# Or use default console output
user = auth(sidebar=True, on_message_cb="default")

# Or silence all messages
user = auth(sidebar=True, on_message_cb=None)
```

The callback receives `(message: str, type: int)` where type is one of:
- `const.INFO` — Informational message
- `const.SUCCESS` — Success message
- `const.WARNING` — Warning message
- `const.ERROR` — Error message

## Architecture & Security

See [`_pm/ARCHITECTURE.md`](./_pm/ARCHITECTURE.md) for detailed technical documentation including:

- **Server-side session tokens** — Why tokens must be stored in the browser (and why that's actually secure)
- **Threat model** — How this design defends against common attacks
- **Component architecture** — Provider pattern, factory pattern, state management
- **Data flow diagrams** — Login, auto-login (cookie), logout flows

## Known Limitations & Considerations

- **Single deployment only** — Not designed for distributed/multi-server deployments (session tokens are server-local)
- **Trusted network** — Assumes users are on a trusted network (no additional encryption between browser and server)
- **No MFA** — Single-factor authentication only (username/password + session token)
- **No password reset** — Use admin.py to change user passwords
- **Email signup requires SendGrid** — No built-in SMTP support

These limitations are intentional trade-offs for simplicity and ease of deployment.

## Future Enhancements

Possible additions (contributions welcome):

- Extended user fields (*created_at*, *last_login*, *logins_count*, etc.)
- Additional auth backends (Auth0, OAuth, SAML)
- Password reset via email link
- Rate limiting on failed logins
- SMTP support as SendGrid alternative
- Database migration tools