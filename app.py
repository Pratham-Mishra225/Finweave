import streamlit as st
from features.nudges import show_nudges
from features.simulations import show_simulations
from features.hive import show_hive

st.set_page_config(page_title="FinWeave", layout="wide")

st.title("💸 FinWeave: Your Mumbai Gig Finance Symbiote")
st.write("Upload data or explore features to get personalized insights powered by Gemini AI!")

tab1, tab2, tab3 = st.tabs(["✨ Nudges", "📈 Simulations", "🐝 Hive"])

with tab1:
    show_nudges()
with tab2:
    show_simulations()
with tab3:
    show_hive()

st.sidebar.title("About")
st.sidebar.info("Powered by **Google Gemini AI**")
