import streamlit as st
import pandas as pd
from utils.gemini_agent import GeminiAgent

agent = GeminiAgent()

def show_hive():
    st.subheader("🐝 Anonymized Peer Insights Hive")

    if st.button("Get Peer Tip", key="hive_button"):
        mock_data = pd.DataFrame({
            "Profile": ["Gig Worker", "Auto Driver"],
            "Savings Tip": [
                "Saved 15% on fuel by carpooling with fellow drivers",
                "Set aside 10% into a monsoon emergency buffer"
            ]
        })
        tip = mock_data.sample(1)["Savings Tip"].values[0]

        prompt = f"Make this savings tip more Mumbai-specific and motivating: {tip}"
        hive_tip = agent.generate(prompt)
        st.warning(f"💡 Hive Insight: {hive_tip}")
