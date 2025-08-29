# Finweave
FinWeave: Mumbai Gig Economy Finance Symbiote
FinWeave is a Streamlit-powered personal finance assistant designed for gig economy workers in Mumbai. It combines AI-powered nudges, what-if scenario simulations, and anonymized peer insights to help users manage volatile income and expenses better.

Features
Proactive Pattern-Based Nudges: Upload your transaction CSV to receive personalized nudges, identifying spending patterns to save smarter.
What-If Scenario Simulations: Explore "what-if" savings or income scenarios that model your financial goals.
Anonymized Peer Insights Hive: Get anonymized peer tips and common patterns from gig workers to improve financial decisions.

Installation
Prerequisites
1)Python 3.12.x (recommended for compatibility and stability)
2)Git
3)A valid Groq API key for AI features

Setup Steps
1)Clone the Repository
text:
git clone <repository-url>
cd finweave-app

2)Create and Activate Virtual Environment
On Windows (PowerShell):
text:
python -m venv .venv
.\.venv\Scripts\Activate.ps1

3)Install Dependencies
text:
pip install -r requirements.txt

4)Setup API Key
Create a .streamlit/secrets.toml file with your Groq API key:
text:
GROQ_API_KEY = "your_actual_groq_api_key_here"

5)Run the App
text:
python -m streamlit run app.py

6)Open Your Browser
Navigate to http://localhost:8501 to access your FinWeave app.

Folder Structure
text:
finweave-app/
├── app.py
├── ai_agent.py
├── features/
│   ├── nudges.py
│   ├── simulations.py
│   └── hive.py
├── tests/
├── requirements.txt
└── .streamlit/
    └── secrets.toml
Usage
Upload a CSV containing transactions with at least columns: Date, Amount, Description.
Explore nudges and simulations to get personalized financial insights.
View anonymized peer insights under the Hive tab.

Troubleshooting
Ensure you have the correct Python version (3.12.x).
Activate the virtual environment where dependencies are installed.
Verify .streamlit/secrets.toml exists and contains your Groq API key.
For any import errors, check your VS Code interpreter points to the correct venv.
If API errors occur, check network and API key validity.

Contributing
Contributions are welcome! Please fork the repo and submit pull requests.

License
MIT License
