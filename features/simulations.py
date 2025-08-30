import streamlit as st
from utils.gemini_agent import GeminiAgent

agent = GeminiAgent()

def show_simulations():
    st.subheader("📈 What-If Scenario Simulations")

    income = st.number_input("Enter your monthly income (₹)", min_value=0, key="sim_income")
    goal = st.number_input("Enter your savings goal (₹)", min_value=0, key="sim_goal")
    months = st.number_input("Timeframe (in months)", min_value=1, key="sim_months")

    if st.button("Run Simulation", key="sim_button"):
        if income > 0 and goal > 0:
            monthly_save = income * 0.1
            time_to_goal = goal / monthly_save if monthly_save else float("inf")

            prompt = f"""
            You earn ₹{income} per month. If you save 10% monthly (₹{monthly_save}),
            how will it affect your goal of saving ₹{goal}? 
            Compare reaching the goal in {time_to_goal:.0f} months vs. delaying it due to overspending.
            Make it relatable for Mumbai gig workers.
            """
            sim = agent.generate(prompt)
            st.info(f"🔮 Simulation: {sim}")
        else:
            st.warning("Please enter valid income and goal values.")
