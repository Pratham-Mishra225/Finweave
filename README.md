# 💸 FinWeave: Your Mumbai Gig Finance Symbiote

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red.svg)](https://streamlit.io/)
[![Gemini AI](https://img.shields.io/badge/Gemini%20AI-Powered-green.svg)](https://ai.google.dev/)

**FinWeave** is an AI-powered financial analytics and simulation platform specifically designed for Mumbai's gig economy workers. It leverages Google's Gemini AI to provide personalized financial insights, proactive nudges, and scenario simulations tailored to the unique challenges faced by gig workers in Mumbai.

## 🚀 Features

### ✨ Proactive Pattern-Based Nudges
- **Smart Transaction Analysis**: Upload your transaction CSV files and get AI-powered insights
- **Mumbai-Specific Recommendations**: Tailored advice for local gig workers
- **Spending Pattern Detection**: Automatically identifies overspending on food delivery, transportation, and other common expenses
- **Real-time Financial Coaching**: Gemini AI provides contextual financial advice

### 📈 What-If Scenario Simulations
- **Income Planning**: Model different income scenarios based on your gig work
- **Savings Goal Tracking**: Set and track progress toward financial goals
- **Time-to-Goal Calculations**: Understand how long it will take to reach your financial objectives
- **Impact Analysis**: See how spending changes affect your long-term financial health

### 🐝 Anonymized Peer Insights Hive
- **Community Wisdom**: Learn from anonymized insights from other gig workers
- **Peer Tips**: Get practical savings and earning tips from the community
- **Local Context**: Mumbai-specific financial strategies and advice
- **Motivational Insights**: Stay motivated with success stories from peers

## 🛠️ Technology Stack

- **Frontend**: Streamlit - Interactive web interface
- **Backend**: Python 3.12
- **AI Engine**: Google Gemini AI (models/gemini-2.5-flash)
- **Data Processing**: Pandas for transaction analysis
- **Environment Management**: python-dotenv for secure API key management

## 📋 Prerequisites

- Python 3.12 or higher
- Google Gemini API key
- Internet connection for AI features

## 🔧 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Pratham-Mishra225/Finweave.git
   cd FINWEAVE
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file in the project root:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

4. **Run the application**:
   ```bash
   streamlit run app.py
   ```

5. **Access the application**:
   Open your browser and navigate to `http://localhost:8501`

## 📁 Project Structure

```
FINWEAVE/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables (create this)
├── features/             # Core application features
│   ├── nudges.py         # Proactive financial nudges
│   ├── simulations.py    # Financial scenario simulations
│   └── hive.py          # Peer insights and community tips
├── utils/               # Utility modules
│   └── gemini_agent.py  # Gemini AI integration
└── sample_data/         # Sample transaction data
    └── transactions.csv # Example transaction format
```

## 🔑 API Configuration

### Getting a Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Create a new API key
4. Copy the API key to your `.env` file

### Supported Models

FinWeave automatically selects the best available Gemini model from:
- `models/gemini-2.5-flash` (preferred)
- `models/gemini-2.0-flash`
- `models/gemini-flash-latest`
- `models/gemini-pro-latest`

## 📊 Transaction Data Format

Upload CSV files with the following columns:

| Column | Description | Example |
|--------|-------------|---------|
| Date | Transaction date | 2024-01-15 |
| Amount | Transaction amount in ₹ | 250.00 |
| Description | Transaction description | Zomato Food Order |

### Sample Data
```csv
Date,Amount,Description
2024-01-15,250.00,Zomato Food Order
2024-01-16,50.00,Auto Rickshaw
2024-01-17,500.00,Grocery Shopping
2024-01-18,300.00,Swiggy Delivery
```

## 🎯 Use Cases

### For Gig Workers
- **Delivery Partners**: Track fuel costs, optimize routes, manage variable income
- **Ride-share Drivers**: Monitor vehicle expenses, plan for maintenance, save for emergencies
- **Freelancers**: Budget for irregular income, plan tax payments, build emergency funds

### For Financial Planning
- **Emergency Fund Planning**: Calculate how much to save for Mumbai's monsoon season
- **Vehicle Maintenance**: Plan for bike/car servicing and repairs
- **Income Optimization**: Identify peak earning periods and plan accordingly

## 🔧 Troubleshooting

### Common Issues

1. **Gemini API Error - Model Not Found**:
   - Solution: The app automatically handles model selection and fallbacks

2. **API Key Not Found**:
   - Ensure your `.env` file is in the correct location
   - Verify the API key format: `GEMINI_API_KEY=your_key_here`

3. **CSV Upload Issues**:
   - Ensure CSV has columns: Date, Amount, Description
   - Check for proper UTF-8 encoding

### Debug Mode

Run the application with debug information:
```bash
streamlit run app.py --logger.level=debug
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google Gemini AI** for providing the intelligent backend
- **Streamlit** for the amazing web framework
- **Mumbai's Gig Community** for inspiring this project

## 📞 Support

For support, questions, or feature requests:
- Create an issue on GitHub
- Contact: [Your Contact Information]

## 🚧 Roadmap

### Upcoming Features
- [ ] Multi-language support (Hindi, Marathi)
- [ ] Integration with UPI payment systems
- [ ] Advanced analytics dashboard
- [ ] Mobile-responsive design
- [ ] Expense categorization with ML
- [ ] Investment recommendations
- [ ] Tax planning tools

### Version History
- **v1.0.0** - Initial release with core features
- **v1.1.0** - Enhanced Gemini AI integration and error handling

---

**Made with ❤️ for Mumbai's Gig Economy**

*FinWeave - Weaving together your financial success, one transaction at a time.*
