import streamlit as st
import pandas as pd
from ai_agent import AIAgent

agent = AIAgent()

def show_nudges():
    st.subheader("Proactive Pattern-Based Nudges")
    uploaded_file = st.file_uploader("Upload transaction CSV (columns: Date, Amount, Description)", type="csv", key="nudges_uploader")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write("Your Transactions:", df.head())

        # Simple pattern detection
        splurges = df[(df['Description'].str.contains('Zomato|Gig', case=False)) & (df['Amount'] > 100)]
        if not splurges.empty:
            try:
                prompt = "Generate a proactive, Mumbai-specific nudge for post-gig splurges: Skip the Chai tapri to save for monsoon cab surges."
                nudge = agent.generate_response(prompt)
                st.success(f"Proactive Nudge: {nudge}")
            except Exception as e:
                st.error(f"Error generating nudge: {e}")
        else:
            st.info("No splurges detected. Try adding more data!")
    else:
        st.info("Upload a CSV to get started.")
