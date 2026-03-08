# Finweave AI 💰

**Finweave AI** is an intelligent financial management application that combines autonomous AI agents with practical financial tools to help users make smarter financial decisions. Built with a FastAPI backend and React Native (Expo) frontend, Finweave provides real-time insights, predictive analytics, and personalized financial guidance.

## 🌟 Key Features

### 🤖 AI-Powered Intelligence

- **Autonomous Agent Loop**: Continuously observes, analyzes, decides, and executes financial actions
- **Event Trigger Engine**: Real-time alerts for income, spending spikes, budget thresholds, and bill reminders
- **Memory Systems**: Learns from past user choices, spending patterns, and financial habits
- **Micro Decision Engine**: AI-powered recommendations for everyday spending decisions
- **Financial Shield Mode**: Proactive protection against overspending and financial risks
- **Stability Score**: Comprehensive financial health metric based on multiple factors

### 📊 Financial Intelligence

- **Income Variability Analysis**: Track and predict income patterns
- **Dynamic Budgeting**: Adaptive budgets that adjust to your spending habits
- **Cash Flow Forecasting**: Predict future financial situations
- **Emergency Buffer Management**: Maintain optimal emergency fund levels
- **Goal Planning**: AI-assisted financial goal setting and tracking
- **Transaction Categorization**: Automatic smart categorization of expenses

### 🛠️ Core Utilities

- **Manual Transaction Entry**: Log cash transactions easily
- **Search & Filtering**: Advanced filtering by date range and amount
- **Monthly/Annual Reports**: Comprehensive financial reporting
- **Spending Heatmaps**: Visual representation of spending patterns
- **Net-worth Tracker**: Monitor total assets minus liabilities
- **Debt Registry**: Track informal debts with friends and family
- **Receipt Scanning**: Capture and attach physical receipts
- **Data Export**: Download transaction history in CSV/PDF format

## 🏗️ Architecture

### Backend (FastAPI)
```
backend/
├── app/
│   ├── main.py              # Application entry point
│   ├── config/              # Configuration and initialization
│   │   ├── firebase.py      # Firebase Authentication
│   │   ├── mongodb.py       # MongoDB connection
│   │   ├── gemini.py        # Google Gemini AI
│   │   └── settings.py      # Environment settings
│   ├── models/              # Pydantic data models
│   │   ├── user.py
│   │   ├── transaction.py
│   │   ├── goal.py
│   │   ├── insight.py
│   │   └── notification.py
│   ├── routers/             # API route handlers
│   │   ├── auth.py
│   │   ├── home.py
│   │   ├── transactions.py
│   │   ├── goals.py
│   │   ├── insights.py
│   │   └── profile.py
│   ├── services/            # Business logic
│   │   ├── ai/
│   │   │   └── gemini_service.py
│   │   ├── transaction_service.py
│   │   ├── goal_service.py
│   │   └── insights_service.py
│   └── utils/               # Utility functions
│       └── auth.py
├── credentials/
│   └── serviceAccount.json  # Firebase Admin SDK credentials
└── requirements.txt
```

### Frontend (React Native - Expo)
```
frontend/
├── app/
│   ├── _layout.jsx          # Root layout
│   ├── login.jsx            # Login screen
│   ├── signup.jsx           # Signup screen
│   ├── (tabs)/              # Tab navigation
│   │   ├── home.jsx         # Dashboard
│   │   ├── transactions.jsx # Transaction list
│   │   ├── goals.jsx        # Goals management
│   │   ├── insights.jsx     # AI insights
│   │   └── profile.jsx      # User profile
│   └── goals/
│       └── add.jsx          # Add goal screen
├── contexts/
│   ├── AuthContext.jsx      # Authentication state
│   └── DashboardContext.jsx # Dashboard state
├── config/
│   └── firebase.js          # Firebase client config
└── assets/
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+** (for backend)
- **Node.js 18+** and npm (for frontend)
- **MongoDB** (local or cloud instance)
- **Firebase Project** (for authentication and Firestore)
- **Google Gemini API Key** (for AI features)

### Backend Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   
   Create a `.env` file in the `backend` directory:
   ```env
   # MongoDB
   MONGODB_URL=mongodb://localhost:27017
   MONGODB_DB_NAME=finweave
   
   # Firebase Admin
   FIREBASE_CREDENTIALS_PATH=credentials/serviceAccount.json
   
   # Google Gemini AI
   GEMINI_API_KEY=your_gemini_api_key_here
   
   # JWT Settings
   JWT_SECRET_KEY=your_secret_key_here
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   
   # CORS
   CORS_ORIGINS=http://localhost:3000,exp://192.168.1.100:8081
   
   # Environment
   ENVIRONMENT=development
   ```

5. **Add Firebase credentials:**
   
   Place your `serviceAccount.json` file in the `backend/credentials/` directory.

6. **Run the backend server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   The API will be available at `http://localhost:8000`
   
   API documentation: `http://localhost:8000/docs`

### Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure Firebase:**
   
   Update `config/firebase.js` with your Firebase project credentials:
   ```javascript
   const firebaseConfig = {
     apiKey: "your_api_key",
     authDomain: "your_auth_domain",
     projectId: "your_project_id",
     storageBucket: "your_storage_bucket",
     messagingSenderId: "your_messaging_sender_id",
     appId: "your_app_id"
   };
   ```

4. **Update API endpoint:**
   
   Configure the backend API URL in your app (typically in an API config file or environment settings).

5. **Start the development server:**
   ```bash
   npm start
   ```

6. **Run on a device/emulator:**
   - Press `a` for Android emulator
   - Press `i` for iOS simulator
   - Scan QR code with Expo Go app on your physical device

## 📱 Running the App

### Development

- **Backend**: `uvicorn app.main:app --reload` (from `backend/` directory)
- **Frontend**: `npm start` (from `frontend/` directory)

### Production

**Backend:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Frontend:**
```bash
npm run build  # For web
npx expo build:android  # For Android
npx expo build:ios  # For iOS
```

## 🔧 Tech Stack

### Backend
- **FastAPI** - Modern, fast web framework for building APIs
- **Firebase Admin SDK** - Authentication and Firestore database
- **MongoDB** - NoSQL database for transaction data
- **Motor** - Asynchronous MongoDB driver
- **Google Gemini AI** - Advanced AI language model
- **Pydantic** - Data validation and settings management
- **Python-Jose** - JWT token handling
- **Passlib** - Password hashing
- **Uvicorn** - ASGI server

### Frontend
- **React Native** - Cross-platform mobile development
- **Expo** - Development platform and tooling
- **Expo Router** - File-based routing for React Native
- **Firebase** - Authentication and cloud services
- **React Native Chart Kit** - Data visualization
- **React Native SVG** - Vector graphics support
- **AsyncStorage** - Local data persistence
- **React Navigation** - Navigation library

## 🔐 Security Features

- **Firebase Authentication**: Secure user authentication
- **JWT Tokens**: Stateless authentication for API requests
- **Password Hashing**: Bcrypt encryption for passwords
- **CORS Protection**: Configured allowed origins
- **Environment Variables**: Sensitive data stored securely
- **Firebase Rules**: Firestore security rules (configure in Firebase Console)

## 📡 API Endpoints

### Authentication
- `POST /auth/signup` - User registration
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `GET /auth/verify` - Verify JWT token

### Transactions
- `GET /transactions` - Get user transactions
- `POST /transactions` - Create new transaction
- `PUT /transactions/{id}` - Update transaction
- `DELETE /transactions/{id}` - Delete transaction

### Goals
- `GET /goals` - Get user goals
- `POST /goals` - Create new goal
- `PUT /goals/{id}` - Update goal
- `DELETE /goals/{id}` - Delete goal

### Insights
- `GET /insights` - Get AI-generated insights
- `GET /insights/spending-analysis` - Detailed spending analysis
- `GET /insights/stability-score` - Financial stability score

### Profile
- `GET /profile` - Get user profile
- `PUT /profile` - Update user profile
- `GET /profile/net-worth` - Calculate net worth

### Notifications
- `GET /notifications` - Get user notifications
- `PUT /notifications/{id}/read` - Mark notification as read

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest test_transactions.py
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📋 Development Roadmap

- [ ] Multi-agent reasoning (Hive feature)
- [ ] Persona mode customization
- [ ] Receipt scanning with OCR
- [ ] Advanced spending simulations
- [ ] Budget threshold alerts
- [ ] Weekly financial planner
- [ ] Risk scoring engine
- [ ] Data export in multiple formats
- [ ] Biometric security options
- [ ] Voice-based transaction entry

## 🐛 Known Issues

Check the [Issues](https://github.com/Pratham-Mishra225/Finweave/issues) page for current bugs and feature requests.

## 📄 License

This project is private and proprietary. All rights reserved.

## 👥 Authors

- **Pratham Mishra** - (https://github.com/Pratham-Mishra225)

## 🙏 Acknowledgments

- Firebase for authentication and database services
- Google Gemini AI for intelligent financial insights
- Expo team for excellent mobile development tools
- FastAPI for the modern Python web framework

## 📧 Contact

For questions or support, please open an issue on GitHub or contact the development team.

---

