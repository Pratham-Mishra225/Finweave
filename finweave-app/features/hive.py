import streamlit as st
import pandas as pd
from ai_agent import AIAgent

agent = AIAgent()

def show_hive():
    st.subheader("Anonymized Peer Insights Hive")
    if st.button("Get Hive Tip", key="hive_button"):
        # Mock aggregated data
        mock_data = pd.DataFrame({
            'Profile': ['Gig Worker', 'Auto Driver'],
            'Savings Tip': ['Saved 15% on fuel by carpooling', 'Diverted 10% to monsoon buffer']
        })
        tip = mock_data.sample(1)['Savings Tip'].values[0]
        try:
            prompt = f"Make this tip Mumbai-specific: {tip} for gig workers."
            hive_tip = agent.generate_response(prompt)
            st.warning(f"Hive Insight: {hive_tip}")
        except Exception as e:
            st.error(f"Error getting hive insight: {e}")
