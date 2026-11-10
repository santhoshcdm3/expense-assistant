# Expense Assistant with Tamil Voice Recognition & Translation

## Features
- **FastAPI Backend**:
  - Add expense records (`POST /expenses`).
  - Retrieve expenses with single-date & date-range filters (`GET /expenses`).
- **Frontend with Tamil Voice Input**:
  - Built-in browser speech recognition configured for **Tamil (`ta-IN`)**.
  - Automatic Tamil-to-English translation & intelligent form auto-fill for amount, title, and category.
  - Date picker & filtering capabilities.

## How to Run

1. **Backend**:
   ```bash
   cd backend
   pip install fastapi uvicorn pydantic
   uvicorn main:app --reload
   ```

2. **Frontend**:
   - Open `frontend/index.html` directly in Google Chrome (or serve via standard static file server).
