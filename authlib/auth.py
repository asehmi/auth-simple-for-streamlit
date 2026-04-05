# see: https://discuss.streamlit.io/t/authentication-script/14111
from os import environ as osenv
import time
from functools import wraps
import logging

import streamlit as st
from streamlit import session_state as state

from . import const, aes256cbcExtended, CookieManager
from .auth_session import AuthSession
from .auth_signup import SignupManager
from .common.email_service import EmailService

# ------------------------------------------------------------------------------
# Globals
ENC_PASSWORD = osenv.get('ENC_PASSWORD')
ENC_NONCE = osenv.get('ENC_NONCE')

STORAGE = osenv.get('STORAGE', 'SQLITE')
COOKIE_NAME = osenv.get('COOKIE_NAME', 'st-auth-simple')
ALLOW_USER_SIGN_UP = osenv.get('ALLOW_USER_SIGN_UP', 'False').lower() == 'true'
store = None
cookie_manager = CookieManager()
# ------------------------------------------------------------------------------

# Wrapping session state in a function ensures that 'user' (or any attribute really) is
# in the session state and, in my opinion, works better with Streamlit's execution model,
# e.g. if state is deleted from cache, it'll be auto-initialized when the function is called
def auth_state():
    if 'user' not in state:
        state.user = None
    if 'skip_cookie_login' not in state:
        state.skip_cookie_login = False
    if 'signup_email' not in state:
        state.signup_email = None
    return state

auth_message = st.empty()
def set_auth_message(msg, type=const.INFO, delay=0.5, show_msgs=True):
    global auth_message
    if type == const.WARNING:
        auth_message = st.warning
    elif type == const.SUCCESS:
        auth_message = st.success
    elif type == const.ERROR:
        auth_message = st.error
    else: # default type == const.INFO:
        auth_message = st.info
    if show_msgs:
        auth_message(msg)
        if delay:
            time.sleep(delay)
            auth_message = st.empty()

# Easy inteceptor for auth
def requires_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if auth_state().user is not None:
            return fn(*args, **kwargs)
        else:
            set_auth_message(f'{fn.__name__} requires authentication!')
    return wrapper

@requires_auth
def logout():
    # Clear server-side token from database FIRST (before browser cookie)
    # If DB clear fails, token remains in DB but is orphaned (security concern, but better than leaving token + cookie)
    db_cleared = False
    if auth_state().user and const.USERNAME in auth_state().user:
        db_cleared = AuthSession.clear_session(store, auth_state().user[const.USERNAME])
        if not db_cleared:
            logging.warning(f"Failed to clear session token for {auth_state().user[const.USERNAME]} during logout")

    # Clear session state
    auth_state().user = None
    auth_state().skip_cookie_login = True  # Skip auto-login on this rerun only

    # Clear browser cookie
    cookie_manager.delete(COOKIE_NAME)

    # Warn user if token wasn't cleared from DB
    if not db_cleared:
        set_auth_message('Warning: Session token could not be cleared from database. Please contact support if you experience login issues.',
                        type=const.WARNING, show_msgs=True, delay=2)

    st.rerun()

def authenticated():
    return auth_state().user is not None

# ------------------------------------------------------------------------------
# Main auth service

def _try_cookie_login():
    """
    Attempt to authenticate from server-side session token.
    Returns True if successful, False otherwise.
    """
    # Skip if user just logged out
    if auth_state().skip_cookie_login:
        auth_state().skip_cookie_login = False
        return False

    # Get token from browser cookie
    token = cookie_manager.get(cookie=COOKIE_NAME)
    if not token:
        return False

    # Validate token against database (token is looked up in DB, user data returned)
    user = AuthSession.validate_session(store, token)
    if user:
        auth_state().user = user
        set_auth_message('Auto-logged in', type=const.SUCCESS, show_msgs=True)
        st.rerun()
        return True
    else:
        # Invalid/expired token
        cookie_manager.delete(COOKIE_NAME)
        return False


def _validate_email(email: str) -> bool:
    """Simple email format validation."""
    import re
    pattern = r'^[^@]+@[^@]+\.[^@]+$'
    return re.match(pattern, email) is not None


def _show_signup_form(show_msgs):
    """Display signup form."""
    set_auth_message('Create your account', delay=None, show_msgs=True)

    with st.form("signup_form", border=True):
        email = st.text_input("Email (will be your username)", value='')
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm password", type="password")
        submit_button = st.form_submit_button("Sign Up", type="primary", use_container_width=False)

    if submit_button:
        _handle_signup_submission(email, password, confirm_password, show_msgs)


def _handle_signup_submission(email: str, password: str, confirm_password: str, show_msgs: bool):
    """Validate signup form and create pending user."""
    # Validate email format
    if not email or not _validate_email(email):
        set_auth_message('Please enter a valid email address', type=const.ERROR, show_msgs=True)
        return

    # Validate passwords match
    if not password or not confirm_password:
        set_auth_message('Password fields cannot be empty', type=const.ERROR, show_msgs=True)
        return

    if password != confirm_password:
        set_auth_message('Passwords do not match', type=const.ERROR, show_msgs=True)
        return

    # Check if email already exists in users table
    ctx = {'fields': '*', 'conds': f'username="{email}"'}
    existing_user = store.query(context=ctx)
    if existing_user:
        set_auth_message('This email is already registered', type=const.ERROR, show_msgs=True)
        return

    # Encrypt password
    encrypted_password = aes256cbcExtended(ENC_PASSWORD, ENC_NONCE).encrypt(password)

    # Create pending user and get PIN
    try:
        pin = SignupManager.create_pending_user(store, email, encrypted_password)
        # Send PIN via email
        if not EmailService.send_signup_pin(email, pin):
            set_auth_message('Failed to send verification email. Please try again.', type=const.ERROR, show_msgs=True)
            return
        # Store email in session state for PIN verification
        auth_state().signup_email = email
        set_auth_message(f'Verification code sent to {email}', type=const.SUCCESS, show_msgs=show_msgs)
        st.rerun()
    except Exception as ex:
        logging.error(f'Signup error: {str(ex)}')
        set_auth_message('An error occurred during signup. Please try again.', type=const.ERROR, show_msgs=True)


def _show_pin_verification_form(show_msgs):
    """Display PIN verification form."""
    set_auth_message(f'Enter the verification code sent to {auth_state().signup_email}', delay=None, show_msgs=True)

    with st.form("pin_form", border=True):
        pin = st.text_input("Verification Code (6 digits)", value='', max_chars=6)
        verify_button = st.form_submit_button("Verify", type="primary", use_container_width=False)

    # Resend button outside form
    if st.button("Resend Code", use_container_width=False):
        user = SignupManager.get_pending_user(store, auth_state().signup_email)
        if user:
            # Regenerate PIN and send
            new_pin = SignupManager.generate_pin()
            store.upsert({
                'table': SignupManager.PENDING_USERS_TABLE,
                'data': {
                    'username': auth_state().signup_email,
                    'password': user['password'],
                    'validation_pin': new_pin,
                    'is_validated': 0,
                    'expires_at': user['expires_at'],
                }
            })
            EmailService.send_signup_pin(auth_state().signup_email, new_pin)
            set_auth_message('New code sent', type=const.SUCCESS, show_msgs=True)
        else:
            set_auth_message('Signup session expired. Please sign up again.', type=const.ERROR, show_msgs=True)
            auth_state().signup_email = None
            st.rerun()

    if verify_button and pin:
        _handle_pin_verification(auth_state().signup_email, pin, show_msgs)


def _handle_pin_verification(email: str, pin: str, show_msgs: bool):
    """Validate PIN and complete signup."""
    success, error_msg = SignupManager.validate_pin(store, email, pin)

    if not success:
        set_auth_message(error_msg, type=const.ERROR, show_msgs=True)
        return

    # PIN is valid, move user to users table
    user = SignupManager.complete_signup(store, email)
    if not user:
        set_auth_message('Failed to complete signup. Please try again.', type=const.ERROR, show_msgs=True)
        return

    # Auto-login
    auth_state().user = user
    auth_state().signup_email = None

    # Create session token for auto-login (remember me)
    token = AuthSession.create_session(store, user, expires_in_days=30)
    if token:
        # Token created successfully, set browser cookie
        cookie_manager.set(COOKIE_NAME, token)
        set_auth_message('Email verified! You are now logged in.', type=const.SUCCESS, show_msgs=show_msgs)
    else:
        # Token creation failed - user is logged in but won't auto-login next time
        set_auth_message('Email verified! You are logged in, but "Remember me" could not be enabled. Please log in again next time.',
                        type=const.WARNING, show_msgs=show_msgs)

    st.rerun()


def _show_login_form(show_msgs):
    """Display and handle the login form."""
    set_auth_message('Please log in', delay=None, show_msgs=True)

    with st.form("login_form", border=True):
        username = st.text_input("Username", value='')
        password = st.text_input("Password", type="password")
        remember_me = st.checkbox("Remember me", value=False)
        submit_button = st.form_submit_button("Login", type="primary", use_container_width=False)

    # Handle form submission
    if submit_button and username and password:
        _handle_login_submission(username, password, remember_me, show_msgs)


def _handle_login_submission(username, password, remember_me, show_msgs):
    """Validate credentials and log user in."""
    # Look up user
    ctx = {'fields': "*", 'conds': f"username=\"{username}\""}
    data = store.query(context=ctx)
    user = data[0] if data else None

    if not user:
        set_auth_message('User not found', type=const.ERROR, show_msgs=True)
        return

    # Verify password
    decrypted_password = aes256cbcExtended(ENC_PASSWORD, ENC_NONCE).decrypt(user[const.PASSWORD])
    if password != decrypted_password:
        set_auth_message('Invalid password', type=const.ERROR, show_msgs=True)
        return

    # Login successful
    auth_state().user = user

    # If "Remember me" checked, create server-side session token
    if remember_me:
        token = AuthSession.create_session(store, user, expires_in_days=30)
        if token:
            # Token created successfully, set browser cookie
            cookie_manager.set(COOKIE_NAME, token)  # Store only the token, not user data
        else:
            # Token creation failed - user is logged in but won't auto-login next time
            logging.warning(f"Failed to create session token for {username} on login")

    set_auth_message('Logging in...', type=const.SUCCESS, show_msgs=show_msgs)
    st.rerun()


def _show_logged_in_ui(sidebar):
    """Display UI for authenticated users."""
    su_widget = st.sidebar.checkbox if sidebar else st.checkbox
    logout_widget = st.sidebar.button if sidebar else st.button

    set_auth_message('Logged in', delay=None, show_msgs=True)

    if logout_widget('Logout'):
        logout()  # logout() calls st.rerun() internally

    if auth_state().user[const.SU] == 1:
        if su_widget("Super users can edit user DB"):
            _superuser_mode()


def auth(sidebar=True, show_msgs=True):
    """
    Main authentication function.
    Flow: Check if authenticated -> Try cookie login -> Show login/signup forms
    """
    global store

    # Initialize storage provider
    if store is None:
        try:
            from authlib.repo.storage_factory import StorageFactory

            store = StorageFactory().get_provider(STORAGE, allow_db_create=False, if_table_exists='ignore')
            ctx = {'fields': "*", 'modifier': "LIMIT 1"}
            store.query(context=ctx)
        except Exception as ex:
            logging.warning(f">>> Storage exception <<<\n`{str(ex)}`")
            store = None
            set_auth_message(
                "Auth DB Not Found. Consider running admin script in standalone mode to generate it."
                "\n\nFor Airtable, ensure the `users` and `pending_users` tables exist and access settings are correct." if STORAGE == 'AIRTABLE' else "",
                type=const.WARNING,
                show_msgs=True
            )

    # Show authentication header
    with st.sidebar if sidebar else st:
        st.subheader('Authentication')

    # Check if already authenticated
    if auth_state().user is not None:
        _show_logged_in_ui(sidebar)
        return auth_state().user[const.USERNAME]

    # Try to auto-login from cookie
    if _try_cookie_login():
        return auth_state().user[const.USERNAME]

    forms_location = st.sidebar if sidebar else st
    with forms_location:
        # Show login and/or signup forms
        if ALLOW_USER_SIGN_UP:
            # Show tabs for login and signup
            login_tab, signup_tab = st.tabs(['Login', 'Sign Up'])

            with login_tab:
                _show_login_form(show_msgs=show_msgs)

            with signup_tab:
                # Check if in middle of signup flow (waiting for PIN)
                if auth_state().signup_email:
                    _show_pin_verification_form(show_msgs=show_msgs)
                else:
                    _show_signup_form(show_msgs=show_msgs)
        else:
            # Only show login form (no signup)
            _show_login_form(show_msgs=show_msgs)

    return auth_state().user[const.USERNAME] if auth_state().user is not None else None


# ------------------------------------------------------------------------------
# Helpers

@requires_auth
def _list_users():
    st.subheader('List users')
    ctx = {'fields': f"{const.USERNAME}, {const.PASSWORD}, {const.SU}"}
    data = store.query(context=ctx)
    if data:
        display_data = [{const.USERNAME: row[const.USERNAME], const.PASSWORD: row[const.PASSWORD], const.SU: row[const.SU]} for row in data]
        st.table(display_data)
    else:
        st.write("`No entries in authentication database`")

@requires_auth
def _create_user(name=const.BLANK, pwd=const.BLANK, is_su=False, mode='create'):
    st.subheader('Create user')
    username = st.text_input("Enter Username (required)", value=name)
    if mode == 'create':
        password = st.text_input("Enter Password (required)", value=pwd, type='password')
    elif mode == 'edit':
        # Do not display password as DB stores them encrypted
        # Passwords will always be created anew in edit mode
        password = st.text_input("Enter Replacement Password (required)", value=const.BLANK)
    su = 1 if st.checkbox("Is this a superuser?", value=is_su) else 0
    if st.button("Update Database") and username:
        if password: # new password given
            encrypted_password = aes256cbcExtended(ENC_PASSWORD, ENC_NONCE).encrypt(password)
        elif mode == 'edit': # reuse old one
            encrypted_password = pwd
        elif mode == 'create': # Must have a password
            st.write("`Database NOT Updated` (enter a password)")
            return
        # TODO: user_id, password, logged_in, expires_at, logins_count, last_login, created_at, updated_at, su
        ctx = {'data': {const.USERNAME: f"{username}", const.PASSWORD: f"{encrypted_password}", const.SU: su}}
        store.upsert(context=ctx)
        st.write("`Database Updated`")

@requires_auth
def _edit_user():
    st.subheader('Edit user')
    ctx = {'fields': const.USERNAME}
    userlist = [row[const.USERNAME] for row in store.query(context=ctx)]
    userlist.insert(0, "")
    username = st.selectbox("Select user", options=userlist)
    if username:
        ctx = {'fields': f"{const.USERNAME}, {const.PASSWORD}, {const.SU}", 'conds': f"{const.USERNAME}=\"{username}\""}
        user_data = store.query(context=ctx)
        _create_user(
            name=user_data[0][const.USERNAME],
            pwd=user_data[0][const.PASSWORD],
            is_su=user_data[0][const.SU],
            mode='edit'
        )

@requires_auth
def _delete_user():
    st.subheader('Delete user')
    ctx = {'fields': const.USERNAME}
    userlist = [row[const.USERNAME] for row in store.query(context=ctx)]
    userlist.insert(0, "")
    username = st.selectbox("Select user", options=userlist)
    if username:
        if st.button(f"Remove {username}"):
            ctx = {'conds': f"{const.USERNAME}=\"{username}\""}
            store.delete(context=ctx)
            st.write(f"`User {username} deleted`")

@requires_auth
def _superuser_mode():
    st.header(f'Super user mode (store = {STORAGE})')
    modes =  {
        "View": _list_users,
        "Create": _create_user,
        "Edit": _edit_user,
        "Delete": _delete_user,
    }
    mode = st.radio("Select mode", modes.keys(), horizontal=True)
    modes[mode]()

# ------------------------------------------------------------------------------
# Allows storage provider to be overriden programmatically 

def override_env_storage_provider(provider):
    try:
        assert(provider in ['SQLITE', 'AIRTABLE'])
        global STORAGE
        STORAGE = provider
    except Exception:
        raise ValueError(f'Unkown provider `{provider}`')

# ------------------------------------------------------------------------------
# Service run from standalone admin app - allows (SQLite) DB to be created

def admin():
    st.warning("Warning, superuser mode")
    if st.checkbox("I accept responsibility and understand this mode can be used to initialise and make changes to the authentication database"):
        from authlib.repo.storage_factory import StorageFactory

        global store
        store = StorageFactory().get_provider(STORAGE, allow_db_create=True, if_table_exists='ignore')

        # Fake the admin user token to enable superuser mode (password field isn't required)
        auth_state().user = {const.USERNAME: 'admin', const.SU: 1}
        _superuser_mode()
