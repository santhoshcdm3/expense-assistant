from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import date

app = FastAPI(title="Expense Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExpenseCreate(BaseModel):
    title: str
    amount: float
    category: str
    expense_date: date  # Format: YYYY-MM-DD

# In-memory database mock (replace with SQLite / database connection)
expenses_db = []

@app.post("/expenses", status_code=201)
def add_expense(expense: ExpenseCreate):
    new_expense = {
        "id": len(expenses_db) + 1,
        "title": expense.title,
        "amount": expense.amount,
        "category": expense.category,
        "expense_date": expense.expense_date.isoformat()
    }
    expenses_db.append(new_expense)
    return {"message": "Expense added successfully", "expense": new_expense}

@app.get("/expenses")
def get_expenses(
    single_date: Optional[date] = Query(None, description="Filter by single date (YYYY-MM-DD)"),
    start_date: Optional[date] = Query(None, description="Filter start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Filter end date (YYYY-MM-DD)")
):
    filtered = expenses_db
    
    # Filter by exact single date
    if single_date:
        filtered = [e for e in filtered if e["expense_date"] == single_date.isoformat()]
    
    # Filter by date range
    elif start_date and end_date:
        filtered = [e for e in filtered if start_date.isoformat() <= e["expense_date"] <= end_date.isoformat()]
    elif start_date:
        filtered = [e for e in filtered if e["expense_date"] >= start_date.isoformat()]
    elif end_date:
        filtered = [e for e in filtered if e["expense_date"] <= end_date.isoformat()]
        
    return {"total_count": len(filtered), "expenses": filtered}
