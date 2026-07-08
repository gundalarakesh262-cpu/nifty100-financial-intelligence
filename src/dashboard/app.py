import sys
from pathlib import Path

import streamlit as st

# MUST be the first Streamlit command
st.set_page_config(
    page_title="Nifty 100 Dashboard",
    page_icon="📈",
    layout="wide"
)

PAGE_ROOT = Path(__file__).resolve().parent
if str(PAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PAGE_ROOT))

# Sidebar
st.sidebar.title("📈 Nifty 100 Platform")

page = st.sidebar.radio(
    "Navigate:",
    [
        "Home",
        "Company Profile",
        "Screener",
        "Sector Analysis",
        "Trends",
        "Reports"
    ]
)

# ---------------- HOME ----------------
if page == "Home":
    st.title("📊 Nifty 100 Financial Intelligence Platform")
    st.write("Welcome to the Nifty 100 Dashboard!")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Companies", "92")

    with col2:
        st.metric("KPIs Available", "50+")

    with col3:
        st.metric("Data Coverage", "2010-2024")

# ---------------- COMPANY PROFILE ----------------
elif page == "Company Profile":
    st.title(" Company Profile")
    st.write("Company specific metrics and details will go here.")

# ---------------- SCREENER ----------------
elif page == "Screener":
    from pages import screener as screener_page
    screener_page.show()

# ---------------- SECTOR ANALYSIS ----------------
elif page == "Sector Analysis":
    import sector_analysis

# ---------------- TRENDS ----------------
elif page == "Trends":
    st.title("📈 Trends")
    st.write("Trend analysis coming soon.")

# ---------------- REPORTS ----------------
elif page == "Reports":
    st.title("📑 Reports")
    st.write("Reports section coming soon.")

st.markdown("---")
st.caption("© 2026 | Nifty 100 Financial Intelligence Platform v1.0")
