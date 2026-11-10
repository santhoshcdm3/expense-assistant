# Expense Assistant Chatbot Full Package

## Contents
- `backend/main.py`: FastAPI application supporting POST/GET operations and date filtering.
- `backend/index_local.html`: Test page that talks to the local FastAPI backend (`http://localhost:8000`).
- `frontend/index.html`: Web Chatbot UI featuring secure SHA-256 passcode verification, Tamil voice input (`ta-IN`), translation API integration, and real-time dashboard analytics. Connected to Oracle APEX (ORDS) so it works when hosted online.
- `netlify.toml`: Netlify configuration (publishes the `frontend` folder).

Oracle APEX endpoints used by `frontend/index.html`:
- `https://oracleapex.com/ords/app_exp/gt/expenses`
- `https://oracleapex.com/ords/app_exp/frmto/exp/dates`

## How to Run (local backend)
1. **Backend**:
   ```
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload --port 8000
   ```
2. **Test page**: open `backend/index_local.html` in Google Chrome and enter your passcode.

## Deploy to Netlify
1. Push this repo to GitHub.
2. Netlify -> Add new site -> Import an existing project -> select the repo.
3. Leave the build command empty. Publish directory is `frontend` (from `netlify.toml`).
4. Deploy, open the site in Chrome (voice input needs Chrome + HTTPS) and enter your passcode.
