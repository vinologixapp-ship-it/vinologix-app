# utils/ui.py
import streamlit as st
import os


def set_page_config(title: str, layout: str = "wide"):
    st.set_page_config(page_title=title, layout=layout)


def apply_global_style():
    st.markdown("""
    <style>
    .block-container { padding-top: 1.0rem; padding-bottom: 1.5rem; }
    section[data-testid="stSidebar"] { background-color: #FFFFFF !important; }
    header[data-testid="stHeader"] { height: 0px; }
    .stMetric { padding: 10px 10px 10px 10px; border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)


def render_sidebar_brand(show_nav_hint: bool = True):
    """
    Logo + hint. Protegido para que NO se dibuje dos veces.
    """
    if st.session_state.get("_brand_rendered", False):
        return

    with st.sidebar:
        # Logo
        if os.path.exists("assets/logo.png"):
            st.image("assets/logo.png", width=160)
        elif os.path.exists("assets/logo.jpg"):
            st.image("assets/logo.jpg", width=160)

        st.markdown("---")

        if show_nav_hint:
            st.caption("📌 Usa el menú lateral para navegar por los módulos.")

    st.session_state["_brand_rendered"] = True