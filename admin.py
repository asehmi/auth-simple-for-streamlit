from os import environ as osenv

import streamlit as st
st.set_page_config(page_title="Simple Auth Admin", layout="wide")

import authlib.auth as auth # noqa
import env # noqa

env.verify()

def main():
    airtable_info = st.empty()

    st.title('Database Admin')

    OPTIONS = ['SQLITE', 'AIRTABLE']
    idx = OPTIONS.index(osenv.get('STORAGE', 'SQLITE'))
    provider = st.sidebar.selectbox('Choose storage provider', OPTIONS, index=idx)

    try:
        auth.override_env_storage_provider(provider)
        auth.admin()
    except Exception as ex:
        st.write('## Trapped exception')
        st.error(str(ex))

    if provider == 'AIRTABLE' and st.sidebar.checkbox('Tell me about Airtable'):
        airtable_info.expander('Getting started with an Airtable database', expanded=True)
        airtable_info.info("Airtable **database creation** is not supported in this application.")
        airtable_info.markdown(
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

            1. You must initially create and then manage your Personal access token the 'Account' overview area
            2. For your base (e.g. `profile`) go to the 'Help menu' and select 'API documentation'
            3. In 'API documentation' select 'METADATA'
            4. In the `curl` example you will see the `appv------X-----c` and reference to `YOUR_SECRET_API_TOKEN` values

                ```bash
                $ curl https://api.airtable.com/v0/appv---X---c/users -H "Authorization: Bearer YOUR_SECRET_API_TOKEN"
                ```
                
                - `YOUR_SECRET_API_TOKEN` is your Personal access token which you should create in the [Developer Hub](https://airtable.com/create/tokens),
                - `YOUR_SECRET_API_TOKEN` is your 'AIRTABLE_PAT',
                - `appv------X-----c` is your 'AIRTABLE_BASE_KEY',
                - `users` will be your 'USERS_TABLE'

            ## Configuring Airtable's app settings 
            
            Assign these values to the keys in the Airtable section of the `.env` file in the application root folder.
            
            For example:

            **.env** file

            ```bash
            # Options are 'SQLITE', 'AIRTABLE'
            STORAGE='AIRTABLE'

            # Airtable account
            AIRTABLE_PAT = 'pat---X---e'
            AIRTABLE_BASE_KEY = 'app---X---c'
            USERS_TABLE = 'users'
            ```

            A full example (which includes SQLite settings) is available in `env.sample`.

            That's it! You're ready now to use the admin application or Airtable directly to manage the credentials of your users.

            ---

            ''',
            unsafe_allow_html=True
        )

c1, c2 = st.columns(2)
with c1:
    main()  