import streamlit as st
import pandas as pd
from utils.gemini_agent import GeminiAgent

agent = GeminiAgent()

def show_nudges():
    st.subheader("✨ Proactive Pattern-Based Nudges")

    uploaded_file = st.file_uploader(
        "Upload your transaction CSV (columns: Date, Amount, Description)", 
        type="csv", 
        key="nudges_upload"
    )

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write("📊 Your Transactions Preview:", df.head())

        splurges = df[
            (df['Description'].str.contains("Zomato|Gig", case=False)) 
            & (df['Amount'] > 100)
        ]

        if not splurges.empty:
            prompt = "Generate a Mumbai-specific financial nudge for gig workers overspending on food and small luxuries."
            nudge = agent.generate(prompt)
            st.success(f"💡 Proactive Nudge: {nudge}")
        else:
            st.info("✅ No splurges detected. Try with more data!")
    else:
        st.info("⬆️ Upload a CSV to start.")
