import streamlit as st
st.set_page_config(page_title="Simple Auth", layout="wide")

import streamlit_debug
streamlit_debug.set(flag=False, wait_for_client=True, host='localhost', port=8765)

import env
env.verify()

from authlib.auth import auth, authenticated, requires_auth
from authlib.common import trace_activity

user = auth(sidebar=True, show_msgs=True)

st.title('Test App')
if authenticated():
    st.success(f'`{user}` is authenticated')
else:
    st.warning(f'Not authenticated')

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

user = auth()  # auth(sidebar=False, show_msgs=False) if you don't want the sidebar, and detailed login messages
\"\"\"This both displays authentication input in the sidebar, and then returns the credentials for use locally\"\"\"

if authenticated():
    st.success(f'{user} is authenticated')
else:
    st.warning(f'Not authenticated')
```
""")
