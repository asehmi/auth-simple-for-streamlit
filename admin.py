from os import environ as osenv

import streamlit as st
st.set_page_config(page_title="Simple Auth Admin", layout="wide")

# Import from st-auth-simple package
import st_auth_simple as auth  # noqa
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
        airtable_info.info("Airtable **database and tables** must be created manually. This admin interface only manages users within existing tables.")
        airtable_info.markdown(
            '''
            # Getting started with an Airtable database

            ## How to create an Airtable

            1. Login to or create a (free) [**Airtable account**](https://airtable.com/account)
            2. Create a base (database) and add the required tables:

            ### USERS table

            | Field | Type | Notes |
            |-------|------|-------|
            | `username` | Single line text | Primary key; stores email |
            | `password` | Single line text | AES256-CBC encrypted |
            | `su` | Number | 0 or 1 (superuser flag) |
            | `auth_token` | Single line text | Session token (empty if not logged in) |
            | `expires_at` | Single line text | ISO format datetime |

            ### PENDING_USERS table *(Optional - only if email signup is enabled)*

            | Field | Type | Notes |
            |-------|------|-------|
            | `username` | Single line text | Email awaiting verification |
            | `password` | Single line text | AES256-CBC encrypted |
            | `validation_pin` | Single line text | 6-digit PIN |
            | `is_validated` | Number | 0 (pending) or 1 (verified) |
            | `expires_at` | Single line text | PIN expiry time (ISO format) |

            ## Finding your Airtable credentials

            1. Create a Personal Access Token in [Developer Hub](https://airtable.com/create/tokens)
            2. For your base, go to Help → API documentation → METADATA
            3. In the curl example, extract:
               - `YOUR_SECRET_API_TOKEN` → Your `AIRTABLE_PAT`
               - `appv---X---c` → Your `AIRTABLE_BASE_KEY`
               - Table names → `USERS_TABLE` and `PENDING_USERS_TABLE` (use uppercase)

            Example curl command:
            ```bash
            curl https://api.airtable.com/v0/appv---X---c/USERS -H "Authorization: Bearer YOUR_SECRET_API_TOKEN"
            ```

            ## Configuring Airtable in .env

            **.env** file
            ```bash
            STORAGE='AIRTABLE'
            AIRTABLE_PAT='pat---X---e'
            AIRTABLE_BASE_KEY='app---X---c'
            USERS_TABLE='USERS'
            PENDING_USERS_TABLE='PENDING_USERS'
            ```

            **Optional: Enable email signup**
            ```bash
            ALLOW_USER_SIGN_UP='True'
            SENDGRID_API_KEY='SG.xxxxx...'
            NOTIFICATION_FROM_EMAIL='noreply@yourapp.com'
            SIGNUP_PIN_EXPIRY_MINUTES='30'
            ```

            See `.env.sample` for a complete example.

            ---

            ''',
            unsafe_allow_html=True
        )

c1, c2 = st.columns(2)
with c1:
    main()  