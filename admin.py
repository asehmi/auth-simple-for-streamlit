import streamlit as st
st.set_page_config(page_title="Simple Auth", layout="wide")

import streamlit_debug
streamlit_debug.set(flag=False, wait_for_client=True, host='localhost', port=8765)

import env
env.verify()

about_airtable = st.sidebar.checkbox('Tell me about Airtable')
if about_airtable:
    expando = st.expander('Getting started with an Airtable database', expanded=True)
    expando.info("Airtable **database creation** is not supported in this application.")
    expando.markdown(
        '''
        # Getting started with an Airtable database
        
        ## How to create an Airtable

        1. First, login into or create a (free) [**Airtable account**](https://airtable.com/account).
        2. Next, follow these steps to create an Airtable:

        - Create a database (referred to as a _base_ in Airtable) and a table within the base.
        - You can call the base `profile` and the table `users`
        - Rename the primary key default table field (aka column) to `username` (field type 'Single line text')
        - Add a `password` field (field type 'Single line text')
        - Add a `su` (superuser) field (field type 'Number')

        ## Finding your Airtable settings

        1. You can initially create and then manage your API key in the 'Account' overview area
        2. For your base (e.g. `profile`) go to the 'Help menu' and select 'API documentation'
        3. In 'API documentation' select 'METADATA'
        4. Check 'show API key' in the code examples panel, and you will see something like this:

        <pre>
        EXAMPLE USING QUERY PARAMETER
        $ curl https://api.airtable.com/v0/appv------X-----c/users?api_key=keyc------X-----i
        </pre>

        - `keyc------X-----i` is your 'API_KEY' (also in your 'Account' area)
        - `appv------X-----c` is your 'BASE_ID',
        - `users` will be your 'TABLE_NAME'

        ## Configuring Airtable's app settings 
        
        Assign these values to the keys in the Airtable section of the `.env` file in the application root folder.
        
        For example:

        **.env** file
        <pre>
        # Options are 'SQLITE', 'AIRTABLE'
        STORAGE='AIRTABLE'

        # Airtable account
        AIRTABLE_API_KEY='keyc------X-----i'
        AIRTABLE_PROFILE_BASE_ID = 'appv------X-----c'
        USERS_TABLE = 'users'
        </pre>

        A full example (which includes SQLite settings) is available in `env.sample`.

        That's it! You're ready now to use the admin application or Airtable directly to manage the credentials of your users.
        ''',
        unsafe_allow_html=True
    )

import authlib.auth as auth
st.title('Database Admin')
auth.admin()
