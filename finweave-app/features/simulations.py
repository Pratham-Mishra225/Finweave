import streamlit as st
from ai_agent import AIAgent

agent = AIAgent()

def show_simulations():
    st.subheader("What-If Scenario Simulations")
    income = st.number_input("Enter monthly income (₹)", min_value=0, key="sim_income")
    spend_goal = st.number_input("Enter savings goal (₹)", min_value=0, key="sim_goal")
    months = st.number_input("In how many months?", min_value=1, key="sim_months")

    if st.button("Simulate", key="sim_button"):
        if income > 0 and spend_goal > 0:
            monthly_save = income * 0.1
            time_to_goal = spend_goal / monthly_save if monthly_save > 0 else float('inf')
            try:
                prompt = f"Generate a text simulation: If you save 10% from {income}, you'll afford a Diwali trip in {time_to_goal:.0f} months vs. overspending delaying it."
                sim = agent.generate_response(prompt)
                st.info(f"Simulation: {sim}")
            except Exception as e:
                st.error(f"Error running simulation: {e}")
        else:
            st.warning("Please enter valid income and goal values.")
