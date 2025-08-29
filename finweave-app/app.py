import streamlit as st

# Import features
from features.nudges import show_nudges
from features.simulations import show_simulations
from features.hive import show_hive

st.title("FinWeave: Your Mumbai Gig Finance Symbiote")
st.write("Upload data or explore features to get personalized insights!")

# Use tabs for easy navigation
tab1, tab2, tab3 = st.tabs(["Nudges", "Simulations", "Hive"])

with tab1:
    show_nudges()

with tab2:
    show_simulations()

with tab3:
    show_hive()

# Optional: Sidebar for app info
st.sidebar.write("Powered by Groq AI (openai/gpt-oss-20b model)")
