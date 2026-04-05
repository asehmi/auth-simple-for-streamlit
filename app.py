from authlib.common import const
import env # noqa

import streamlit as st
# Must be called before importing st_auth_simple, which is also a Streamlit file
st.set_page_config(page_title="Simple Auth", layout="wide")

# Import from st-auth-simple package
from st_auth_simple import auth, authenticated, requires_auth  # noqa
# from authlib.common import trace_activity

env.verify()

def auth_message_cb(msg, type=const.INFO):
    if type == const.WARNING:
        st.toast(msg, icon="⚠️", duration="long")
    elif type == const.SUCCESS:
        st.toast(msg, icon="✅", duration="short")
    elif type == const.ERROR:
        st.toast(msg, icon="❌", duration="long")
    else: # default type == const.INFO:
        st.toast(msg, icon="ℹ️", duration="short")  

# auth(sidebar=False, on_message_cb=None) if you don't want the sidebar, and detailed login messages
user = auth(sidebar=True, on_message_cb=auth_message_cb)

st.title('Test App')
if authenticated():
    st.success(f'`{user}` is authenticated')
else:
    st.warning('Not authenticated')

st.markdown(
"""
## About
---
This is a landing page designed to showcase the simple authentication library.

This is just a single import and a function to run, and the return value is either None,
or the authenticated username.

The user login is usually based in the sidebar (though ultimately configurable by passing True or False 
to the sidebar parameter of the auth function

All the user management and username and password entry should be taken care of by the library. To automatically 
have creation and edit access, just run the library directly as a streamlit script.

```python
from authlib.auth import auth, authenticated

user = auth()  # auth(sidebar=False, on_message_cb=None) if you don't want the sidebar, and detailed login messages
\"\"\"This both displays authentication input in the sidebar, and then returns the credentials for use locally\"\"\"

if authenticated():
    st.success(f'{user} is authenticated')
else:
    st.warning(f'Not authenticated')
```
""")
