"""Shared sidebar navigation for the multipage app."""
import streamlit as st


def render_sidebar_navigation():
    """Render custom page links with stable labels/icons.

    This is used with `showSidebarNavigation = false` so we can control the
    labels even when the entrypoint file is named `app.py` for deployment.
    """
    st.sidebar.page_link("app.py", label="🏠 Home")
    st.sidebar.page_link("pages/1_👥 Who writes the most?.py", label="👥 Who writes the most?")
    st.sidebar.page_link("pages/2_📝Words.py", label="📝 Words")
    st.sidebar.page_link("pages/4_😊 Sentiment.py", label="😊 Sentiment")
