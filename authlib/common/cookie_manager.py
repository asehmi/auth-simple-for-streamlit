import datetime
import streamlit as st
import extra_streamlit_components as stx

class CookieManager():

    def __init__(self):
        pass

    @staticmethod
    @st.experimental_singleton
    def get_manager():
        return stx.CookieManager()

    def get(self, cookie: str):
        return CookieManager.get_manager().get(cookie)

    def set(self, cookie, val, expires_at=datetime.datetime.now() + datetime.timedelta(days=1),
            key="set"):
        return CookieManager.get_manager().set(cookie=cookie, val=val, expires_at=expires_at, key=key)

    def delete(self, cookie, key="delete"):
        return CookieManager.get_manager().delete(cookie=cookie, key=key)

    def get_all(self, key="get_all"):
        return CookieManager.get_manager().get_all()
