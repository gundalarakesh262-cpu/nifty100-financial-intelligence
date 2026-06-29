import streamlit as st

st.set_page_config(
    page_title="Nifty 100 Dashboard",
    page_icon="",
    layout="wide"
)

st.title(" Nifty 100 Financial Intelligence Platform")
st.write("Welcome to the Nifty 100 Dashboard!")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Companies", "92")
with col2:
    st.metric("KPIs Available", "50+")
with col3:
    st.metric("Data Coverage", "2010-2024")

st.success(" Dashboard is live")