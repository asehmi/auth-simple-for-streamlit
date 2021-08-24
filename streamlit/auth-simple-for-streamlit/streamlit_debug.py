import streamlit as st

_DEBUG = False
def set(flag: bool=False, wait_for_client=False, host='localhost', port=8765):
    global _DEBUG
    _DEBUG = flag
    try:
        # To prevent debugpy loading again and again because of
        # Streamlit's execution model, we need to track debugging state 
        if 'debugging' not in st.session_state:
            st.session_state.debugging = False

        if _DEBUG and not st.session_state.debugging:
            # https://code.visualstudio.com/docs/python/debugging
            import debugpy
            debugpy.listen((host, port))
            if wait_for_client:
                debugpy.wait_for_client() # Only include this line if you always want to manually attach the debugger
            # debugpy.breakpoint()
            st.session_state.debugging = True

            print(f'>>> Remote debugging activated (host={host}, port={port}) <<<')
        
        if not _DEBUG:
            st.session_state.debugging = False
    except:
        # Ignore... e.g. for cloud deployments
        pass
