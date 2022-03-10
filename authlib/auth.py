# see: https://discuss.streamlit.io/t/authentication-script/14111
from os import environ as osenv
import time
from functools import wraps
import logging

import streamlit as st

from . import const, aes256cbcExtended, CookieManager

# ------------------------------------------------------------------------------
# Globals
ENC_PASSWORD = osenv.get('ENC_PASSWORD')
ENC_NONCE = osenv.get('ENC_NONCE')

STORAGE = osenv.get('STORAGE', 'SQLITE')
COOKIE_NAME = osenv.get('COOKIE_NAME')
store = None
cookie_manager = CookieManager()
# ------------------------------------------------------------------------------

# Wrapping session state in a function ensures that 'user' (or any attribute really) is
# in the session state and, in my opinion, works better with Streamlit's execution model,
# e.g. if state is deleted from cache, it'll be auto-initialized when the function is called
def auth_state():
    if 'user' not in st.session_state:
        st.session_state.user = None
    return st.session_state

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
        if auth_state().user != None:
            return fn(*args, **kwargs)
        else:
            set_auth_message(f'{fn.__name__} requires authentication!')
    return wrapper

@requires_auth
def logout():
    auth_state().user = None
    cookie_manager.delete(COOKIE_NAME)

def authenticated():
    return auth_state().user != None

# ------------------------------------------------------------------------------
# Main auth service

def _auth(sidebar=True, show_msgs=True):

    global store
    if store == None:
        try:
            from authlib.repo.storage_factory import StorageFactory

            # get the store
            store = StorageFactory().get_provider(STORAGE, allow_db_create=False, if_table_exists='ignore')
            # check the table
            ctx = {'fields': "*", 'modifier': "LIMIT 1"}
            store.query(context=ctx)
        except Exception as ex:
            logging.warning(f">>> Storage exception <<<\n`{str(ex)}`")
            store = None
            set_auth_message(
                "Auth DB Not Found. Consider running admin script in standalone mode to generate it.",
                type=const.WARNING,
                show_msgs=True
            )

    header_widget = st.sidebar.subheader if sidebar else st.subheader
    username_widget = st.sidebar.text_input if sidebar else st.text_input
    password_widget = st.sidebar.text_input if sidebar else st.text_input
    remember_me_widget = st.sidebar.checkbox if sidebar else st.checkbox
    su_widget = st.sidebar.checkbox if sidebar else st.checkbox
    logout_widget = st.sidebar.button if sidebar else st.button

    header_widget('Authentication')

    if auth_state().user == None:

        # cookie login
        cookie_manager.get_all()
        user_in_cookie = cookie_manager.get(cookie=COOKIE_NAME)
        if user_in_cookie:
            ctx={'fields': "*", 'conds': f"username=\"{user_in_cookie[const.USERNAME]}\""}
            data = store.query(context=ctx)
            user = data[0] if data else None
            # After checking for the presence of a user name, encrypted passwords are compared with each other.
            if user and user[const.PASSWORD] == user_in_cookie[const.PASSWORD]:
                auth_state().user = user
                set_auth_message('Logging in...', type=const.SUCCESS, show_msgs=show_msgs)
                st.experimental_rerun()

        set_auth_message('Please log in', delay=None, show_msgs=True)

        username = username_widget("Enter username", value='')

        ctx={'fields': "*", 'conds': f"username=\"{username}\""}
        data = store.query(context=ctx)
        user = data[0] if data else None
        if user:
            decrypted_password = aes256cbcExtended(ENC_PASSWORD, ENC_NONCE).decrypt(user[const.PASSWORD])
            password = password_widget("Enter password", type="password")
            if password == decrypted_password:
                # TODO: set active state and other fields then update DB
                # Update user state, password is encrypted so secure
                auth_state().user = user
                set_auth_message('Logging in...', type=const.SUCCESS, show_msgs=show_msgs)
                st.experimental_rerun()

    if auth_state().user != None:
        set_auth_message('Logged in', delay=None, show_msgs=True)
        if logout_widget('Logout'):
            logout()
            set_auth_message('Logging out...', type=const.WARNING, show_msgs=show_msgs)
            st.experimental_rerun()
        if auth_state().user[const.SU] == 1:
            if su_widget(f"Super users can edit user DB"):
                _superuser_mode()
        if cookie_manager.get(cookie=COOKIE_NAME):
            if not remember_me_widget("Remember me", value=True):
                cookie_manager.delete(COOKIE_NAME)
        else:
            if remember_me_widget("Remember me", value=False):
                cookie_manager.set(COOKIE_NAME, auth_state().user)

    return auth_state().user[const.USERNAME] if auth_state().user != None else None

def auth(*args, **kwargs):
    with st.expander('Authentication', expanded=True):
        return _auth(*args, **kwargs)

# ------------------------------------------------------------------------------
# Helpers

@requires_auth
def _list_users():
    st.subheader('List users')
    ctx = {'fields': "username, password, su"}
    data = store.query(context=ctx)
    if data:
        st.table(data)
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
        ctx = {'data': {"username": f"{username}", "password": f"{encrypted_password}", "su": su}}
        store.upsert(context=ctx)
        st.write("`Database Updated`")

@requires_auth
def _edit_user():
    st.subheader('Edit user')
    ctx = {'fields': "username"}
    userlist = [row[const.USERNAME] for row in store.query(context=ctx)]
    userlist.insert(0, "")
    username = st.selectbox("Select user", options=userlist)
    if username:
        ctx = {'fields': "username, password, su", 'conds': f"username=\"{username}\""}
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
    ctx = {'fields': "username"}
    userlist = [row[const.USERNAME] for row in store.query(context=ctx)]
    userlist.insert(0, "")
    username = st.selectbox("Select user", options=userlist)
    if username:
        if st.button(f"Remove {username}"):
            ctx = {'conds': f"username=\"{username}\""}
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
    mode = st.radio("Select mode", modes.keys())
    modes[mode]()

# ------------------------------------------------------------------------------
# Allows storage provider to be overriden programmatically 

def override_env_storage_provider(provider):
    try:
        assert(provider in ['SQLITE', 'AIRTABLE'])
        global STORAGE
        STORAGE = provider
    except:
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
        auth_state().user = {'username': 'admin', 'su': 1}
        _superuser_mode()
