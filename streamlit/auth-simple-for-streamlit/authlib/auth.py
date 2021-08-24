# see: https://discuss.streamlit.io/t/authentication-script/14111
from os import environ as osenv
import time
from functools import wraps
import logging

import streamlit as st

from . import const

# ------------------------------------------------------------------------------
# Globals
STORAGE = osenv.get('STORAGE', 'SQLITE')
store = None
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
            store.query(fields="*", modifier="LIMIT 1")
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
    su_widget = st.sidebar.checkbox if sidebar else st.checkbox
    logout_widget = st.sidebar.button if sidebar else st.button

    header_widget('Authentication')

    if auth_state().user == None:
        set_auth_message('Please log in', delay=None, show_msgs=True)

        user = username_widget("Enter username", value='')

        data = store.query(fields="*", conds=f"username=\"{user}\"")
        user = data[0] if data else None
        if user:
            password = password_widget("Enter password", type="password")
            if password == user[const.PASSWORD]:
                # TODO: set active state and other fields then update DB
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

    return auth_state().user[const.USERNAME] if auth_state().user != None else None

def auth(*args, **kwargs):
    with st.expander('Authentication', expanded=True):
        return _auth(*args, **kwargs)

# ------------------------------------------------------------------------------
# Helpers

@requires_auth
def _list_users():
    st.subheader('List users')
    data = store.query(fields="username, password, su")
    if data:
        st.table(data)
    else:
        st.write("`No entries in authentication database`")

@requires_auth
def _create_user(name="", pwd="", is_su=False):
    st.subheader('Create user')
    username = st.text_input("Enter Username", value=name)
    password = st.text_input("Enter Password (required)", value=pwd)
    su = 1 if st.checkbox("Is this a superuser?", value=is_su) else 0
    if st.button("Update Database") and username and password:
        store.upsert(data={"username": f"{username}", "password": f"{password}", "su": su})
        # user_id, password, logged_in, expires_at, logins_count, last_login, created_at, updated_at, su
        st.write("`Database Updated`")

@requires_auth
def _edit_user():
    st.subheader('Edit user')
    userlist = [row[const.USERNAME] for row in store.query(fields="username")]
    userlist.insert(0, "")
    edit_user = st.selectbox("Select user", options=userlist)
    if edit_user:
        user_data = store.query(fields="username, password, su", conds=f"username=\"{edit_user}\"")
        _create_user(
            name=user_data[0][const.USERNAME],
            pwd=user_data[0][const.PASSWORD],
            is_su=user_data[0][const.SU]
        )

@requires_auth
def _delete_user():
    st.subheader('Delete user')
    userlist = [row[const.USERNAME] for row in store.query(fields="username")]
    userlist.insert(0, "")
    del_user = st.selectbox("Select user", options=userlist)
    if del_user:
        if st.button(f"Remove {del_user}"):
            store.delete(conds=f"username=\"{del_user}\"")
            st.write(f"`User {del_user} deleted`")

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
# Service run from standalone admin app - allows (SQLite) DB to be created

def admin():
    st.error("Warning, superuser mode")
    st.write("Use this mode to initialise authentication database")
    if st.checkbox("Check to continue"):
        from authlib.repo.storage_factory import StorageFactory

        global store
        store = StorageFactory().get_provider(STORAGE, allow_db_create=True, if_table_exists='ignore')

        auth_state().user = {'username': 'admin', 'su': 1}
        _superuser_mode()
