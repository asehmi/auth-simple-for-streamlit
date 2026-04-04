# see: https://discuss.streamlit.io/t/authentication-script/14111
from os import environ as osenv
import time
from functools import wraps
import logging

import streamlit as st
from streamlit import session_state as state

from . import const, aes256cbcExtended, CookieManager
from .auth_session import AuthSession

# ------------------------------------------------------------------------------
# Globals
ENC_PASSWORD = osenv.get('ENC_PASSWORD')
ENC_NONCE = osenv.get('ENC_NONCE')

STORAGE = osenv.get('STORAGE', 'SQLITE')
COOKIE_NAME = osenv.get('COOKIE_NAME', 'st-auth-simple')
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
    # Clear server-side token from database
    if auth_state().user and const.USERNAME in auth_state().user:
        AuthSession.clear_session(store, auth_state().user[const.USERNAME])

    # Clear session state
    auth_state().user = None
    auth_state().skip_cookie_login = True  # Skip auto-login on this rerun only

    # Clear browser cookie
    cookie_manager.delete(COOKIE_NAME)

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


def _show_login_form(sidebar, show_msgs):
    """Display and handle the login form."""
    set_auth_message('Please log in', delay=None, show_msgs=True)

    # Render form in sidebar or main area based on sidebar flag
    form_location = st.sidebar if sidebar else st
    with form_location:
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
        cookie_manager.set(COOKIE_NAME, token)  # Store only the token, not user data

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


def _auth(sidebar=True, show_msgs=True):
    """
    Main authentication function.
    Flow: Check if authenticated -> Try cookie login -> Show login form
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
                "\n\nFor Airtable, ensure the `users` table exists and access settings are correct." if STORAGE == 'AIRTABLE' else "",
                type=const.WARNING,
                show_msgs=True
            )

    # Show authentication header
    header_widget = st.sidebar.subheader if sidebar else st.subheader
    header_widget('Authentication')

    # Check if already authenticated
    if auth_state().user is not None:
        _show_logged_in_ui(sidebar)
        return auth_state().user[const.USERNAME]

    # Try to auto-login from cookie
    if _try_cookie_login():
        return auth_state().user[const.USERNAME]

    # Show login form
    _show_login_form(sidebar, show_msgs)

    return auth_state().user[const.USERNAME] if auth_state().user is not None else None

def auth(*args, **kwargs):
    with st.expander('Authentication', expanded=True):
        return _auth(*args, **kwargs)

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
