# Expense Assistant Chatbot Full Package

## Contents
- `backend/main.py`: FastAPI application supporting POST/GET operations and date filtering.
- `frontend/index.html`: Web Chatbot UI featuring secure SHA-256 passcode verification, Tamil voice input (`ta-IN`), translation API integration, and real-time dashboard analytics.
- `netlify.toml`: Netlify configuration.

## How to Run

1. **Backend**:
   ```bash
   cd backend
   pip install fastapi uvicorn pydantic
   uvicorn main:app --reload --port 8000
   ```

2. **Frontend**:
   - Open `frontend/index.html` in Google Chrome.
   - Enter your passcode to access the chatbot interface.
