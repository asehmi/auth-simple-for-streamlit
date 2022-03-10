import streamlit as st
import extra_streamlit_components as stx

@st.experimental_singleton
def cookie_manager():
    return stx.CookieManager()
