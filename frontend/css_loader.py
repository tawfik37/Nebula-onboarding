"""
CSS Loader Utility
Loads and injects CSS files into Streamlit app
"""
from pathlib import Path
import streamlit as st


def get_css_path(filename: str) -> Path:
    """Get the absolute path to a CSS file in the styles directory."""
    current_dir = Path(__file__).parent
    css_path = current_dir / "assets" / "styles" / filename
    return css_path


def load_css_file(filename: str) -> str:
    """Load CSS content from a file."""
    css_path = get_css_path(filename)

    if not css_path.exists():
        st.warning(f"CSS file not found: {filename}")
        return ""

    try:
        with open(css_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        st.error(f"Error loading CSS file {filename}: {e}")
        return ""


def load_all_css() -> str:
    """
    Load all CSS files in the correct order.
    Returns combined CSS as a single string.
    """
    css_files = [
        'theme.css',      # Variables first
        'base.css',       # Base styles
        'animations.css', # Animations
        'components.css', # Components
        'chat.css',       # Chat interface
        'sidebar.css',    # Sidebar
    ]

    combined_css = ""
    for css_file in css_files:
        css_content = load_css_file(css_file)
        if css_content:
            combined_css += f"\n/* {css_file} */\n{css_content}\n"

    return combined_css


def inject_css():
    """Inject all CSS into the Streamlit app."""
    css = load_all_css()

    if css:
        st.markdown(f"""
        <style>
        {css}
        </style>
        """, unsafe_allow_html=True)
    else:
        st.warning("No CSS loaded. Using default Streamlit styling.")


def inject_custom_css(css_string: str):
    """Inject custom CSS string directly."""
    st.markdown(f"""
    <style>
    {css_string}
    </style>
    """, unsafe_allow_html=True)
