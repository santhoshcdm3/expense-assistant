try:
    from curl_cffi import requests as http_requests
    USE_CURL_CFFI = True
except ImportError:
    import requests as http_requests
    USE_CURL_CFFI = False
import pandas as pd
import re
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo


# =====================================================================
#  ORIGINAL LOGIC (UNCHANGED)
# =====================================================================

sample_data = {
    "GET_EXPENSE": [
        "show yesterday expenses",
        "what did I spend yesterday",
        "get my expenses",
        "show my recent transactions",
        "display today's expenses",
        "நேற்று நான் என்ன செலவு செய்தேன்",
        "get the expense of date 10/10/2026",
        "show expenses for 10/10/2026"
    ],

    "ADD_EXPENSE": [
        "add a new expense",
        "I spent 500 for dinner",
        "i had spend 500 for dinner on sbi credit card yesterday",
        "record my food expense",
        "add 300 for shopping",
        "I paid 1000 for lunch",
        "spent 61rs for amrutanjan roll on in hdfc card for me today",
        "add expense 500 for dinner using upi",
        "paid 250 for groceries yesterday"
    ],

    "GET_DATE_RANGE": [
        "show expenses between two dates",
        "get last 15 days expenses",
        "show this month's expenses",
        "get expenses from October 1 to October 30",
        "show expenses from 01/10/2025 to 31/12/2025",
        "Please show expenses from 01/10/2025 to 31/12/2025"
    ],

    "GET_PERSON_EXPENSE": [
        "how much did I spend for Manikandan",
        "show person wise expenses",
        "how much does each person owe me",
        "show expenses for each person"
    ],

    "GET_CARD_EXPENSE": [
        "show HDFC card expenses",
        "how much did I spend using HDFC",
        "show credit card transactions"
    ],

    "EXPENSE_ANALYSIS": [
        "analyze my expenses",
        "give me spending insights",
        "analyze my last 15 days spending",
        "where did I spend the most money"
    ]
}


def word_emmbedding(prompt):
    words = re.sub(r'[^a-zA-Z0-9]', ' ', prompt)
    words = words.lower().split()
    return words


def chatbot_proc2(cp_text):
    stop_words = [
        "what", "which", "who", "whose", "where", "when",
        "why", "how", "is", "are", "am", "was", "were",
        "do", "does", "did", "has", "have", "had", "can",
        "could", "shall", "should", "will", "would", "may",
        "might", "must", "give", "tell", "find",
        "explain", "describe", "define", "provide",
        "a", "an", "the", "of", "for",
        "with", "by", "in", "on", "at",
        "into", "onto", "over", "under",
        "through", "during", "before", "after",
        "above", "below",
        "and", "or", "but", "because", "while",
        "although",
        "i", "you", "he", "she", "it", "we",
        "they", "me", "him", "her", "us", "them",
        "my", "your", "his", "their", "our",
        "this", "that", "these", "those",
        "about", "regarding", "related",
        "regards", "information", "details", "data",
        "records", "result", "results",
        "answer", "answers", "want", "please"
    ]

    return [word for word in cp_text if word.lower() not in stop_words]


def chatbot_proc1(cp_text):
    cp_text = re.sub(r"[^\w/'-]", " ", cp_text, flags=re.UNICODE)
    cp_text = cp_text.lower().split()
    return " ".join(chatbot_proc2(cp_text))


sentences = []
labels = []

for intent, examples in sample_data.items():
    for sentence in examples:
        sentences.append(chatbot_proc1(sentence))
        labels.append(intent)

vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 2))
X = vectorizer.fit_transform(sentences)


def india_today():
    return datetime.now(ZoneInfo("Asia/Kolkata")).date()


def predict_intent(sample_text):
    # Explicit rules make short queries such as "today expense" reliable.
    text = sample_text.lower().strip()
    date_pattern = r"(?<!\d)\d{1,2}[/-]\d{1,2}[/-]\d{2,4}(?!\d)"
    date_count = len(re.findall(date_pattern, text))

    if date_count >= 2 or any(x in text for x in ("last 15 days", "last 7 days", "this month", "last month", "date range")):
        return "GET_DATE_RANGE", 1.0
    if any(x in text for x in ("add expense", "record expense", "i spent", "i spend", "i paid", "paid ", "spent ", "bought ")):
        return "ADD_EXPENSE", 1.0
    if any(x in text for x in ("person wise", "each person", "owe me", "for manikandan")):
        return "GET_PERSON_EXPENSE", 1.0
    if any(x in text for x in ("analyze", "analysis", "spending insights", "spent the most")):
        return "EXPENSE_ANALYSIS", 1.0
    if any(x in text for x in ("card expense", "credit card", "hdfc card", "sbi card")) and any(x in text for x in ("show", "get", "how much", "expense", "spent")):
        return "GET_CARD_EXPENSE", 1.0
    has_expense = any(x in text for x in ("expense", "expenses", "spend", "spent", "transaction", "transactions"))
    has_date = date_count > 0 or any(x in text for x in ("today", "yesterday", "tomorrow", "recent", "last monday", "last tuesday", "last wednesday", "last thursday", "last friday", "last saturday", "last sunday"))
    if has_expense and has_date:
        return "GET_EXPENSE", 1.0

    cleaned = chatbot_proc1(sample_text)
    user_vector = vectorizer.transform([cleaned])
    scores = cosine_similarity(user_vector, X)[0]
    best_index = scores.argmax()
    confidence = float(scores[best_index])
    if confidence < 0.20:
        return "UNKNOWN", confidence
    return labels[best_index], confidence


def word_extraction(prompt):

    persons = {
        'ramya': 104,
        'family': 108,
        'manikandanrs': 106,
        'santhosh': 100,
        'me': 100,
        'mohamed': 101,
        'gowtham': 102,
        'vinoth': 103,
        'priya': 111,
        'subasri': 105,
        'manikandanrtr': 107
    }

    exp_dates = {
        'today': india_today(),
        'yesterday': india_today() - timedelta(days=1),
        'tomorrow': india_today() + timedelta(days=1)
    }

    bank = {
        'axics card': 501,
        'axics': 501,
        'sbi credit card': 503,
        'sbi card': 503,
        'sbi': 503,
        'tata neu': 500,
        'hdfc': 500,
        'icic': 502,
        'scapia': 504,
        'federal': 504
    }

    sub_type = {
        'upi': 'upi',
        'card': 'card',
        'credit card': 'card',
        'cash': 'cash'
    }

    p_person = []
    p_expense_type = None
    p_exp_date = None
    p_sub_type = None
    p_paid_by = 100
    p_amount = None
    p_desc = None

    text = prompt.lower()
    words = word_emmbedding(prompt)

    # 1. Extract persons (preserve order, avoid duplicates)
    for token in words:
        if token in persons:
            person_id = persons[token]
            if person_id not in p_person:
                p_person.append(person_id)

    # 2. Extract bank (longest matching phrase first)
    for bank_name in sorted(bank, key=len, reverse=True):
        if re.search(r'\b' + re.escape(bank_name) + r'\b', text):
            p_expense_type = bank[bank_name]
            break

    # 3. Extract relative date
    for token in words:
        if token in exp_dates:
            p_exp_date = exp_dates[token]
            break

    # 4. Extract numeric date if relative date was not found
    date_pattern = r'(?<!\d)\d{1,2}[/-]\d{1,2}[/-]\d{2,4}(?!\d)'
    date_match = re.search(date_pattern, text)

    if p_exp_date is None and date_match:
        date_value = date_match.group()
        date_format = (
            '%d/%m/%y' if '/' in date_value and len(date_value.split('/')[-1]) == 2
            else '%d/%m/%Y' if '/' in date_value
            else '%d-%m-%y' if len(date_value.split('-')[-1]) == 2
            else '%d-%m-%Y'
        )

        try:
            p_exp_date = datetime.strptime(date_value, date_format).date()
        except ValueError:
            p_exp_date = None

    if p_exp_date:
        p_exp_date = p_exp_date.strftime('%d/%m/%Y')

    # 5. Extract payment mode (longest matching phrase first)
    for mode in sorted(sub_type, key=len, reverse=True):
        if re.search(r'\b' + re.escape(mode) + r'\b', text):
            p_sub_type = sub_type[mode]
            break

    # 6. Extract amount after removing numeric date
    amount_text = text

    if date_match:
        amount_text = amount_text.replace(date_match.group(), ' ', 1)

    amount_match = re.search(
        r'(?<!\d)(\d+(?:\.\d+)?)\s*(?:rs|rupees)?\b',
        amount_text
    )

    if amount_match:
        amount_number = float(amount_match.group(1))
        p_amount = int(amount_number) if amount_number.is_integer() else amount_number

    # 7. Extract description
    description_match = re.search(
        r'\bfor\s+(.+?)(?=\s+\b(?:on|using|via|with)\b|$)',
        text
    )

    if description_match:
        description_text = description_match.group(1).strip()

        for person_name in sorted(persons, key=len, reverse=True):
            description_text = re.sub(
                r'\b' + re.escape(person_name) + r'\b',
                ' ',
                description_text
            )

        description_text = re.sub(
            r'\b\d+(?:\.\d+)?\s*(?:rs|rupees)?\b',
            ' ',
            description_text
        )
        description_text = re.sub(r'\s+', ' ', description_text).strip(' ,.-')

        if description_text:
            p_desc = description_text

    # 8. Build payload
    persons_payload = ','.join(str(person_id) for person_id in p_person) if p_person else None

    extracted_data = {
        "P2_FOR_PERSONS": persons_payload,
        "P2_EXPENSE_DATE": p_exp_date,
        "P2_DESCRIPTION": p_desc,
        "P2_AMOUNT": p_amount,
        "P2_PAID_BY": p_paid_by,
        "P2_EXPENSE_TYPE": p_expense_type,
        "P2_SUB_TYPE": p_sub_type,
        "P2_CREATED_BY": "Santhosh"
    }

    # 9. Validate required fields
    required_fields = [
        "P2_FOR_PERSONS",
        "P2_EXPENSE_DATE",
        "P2_DESCRIPTION",
        "P2_AMOUNT",
        "P2_PAID_BY",
        "P2_EXPENSE_TYPE",
        "P2_SUB_TYPE",
        "P2_CREATED_BY"
    ]

    missing_values = [
        key for key in required_fields
        if extracted_data.get(key) is None or extracted_data.get(key) == ''
    ]

    print("\nExtracted API Payload:")
    for key, value in extracted_data.items():
        print(f"{key}: {value}")

    if missing_values:
        print("\nMissing fields:")
        for field in missing_values:
            print(field)
    else:
        print("\nAll parameters identified!")

    return extracted_data, missing_values


def parse_date_string(date_value):
    for fmt in ('%d/%m/%Y', '%d/%m/%y', '%d-%m-%Y', '%d-%m-%y'):
        try:
            return datetime.strptime(date_value, fmt).strftime('%d/%m/%Y')
        except ValueError:
            pass
    return None


def extract_date(sample_text):
    sample_text = sample_text.lower()
    today = india_today()

    if re.search(r'\btoday\b', sample_text):
        return today.strftime('%d/%m/%Y')

    if re.search(r'\byesterday\b', sample_text):
        return (today - timedelta(days=1)).strftime('%d/%m/%Y')

    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6
    }

    for day, day_number in weekdays.items():
        if "last " + day in sample_text:
            difference = (today.weekday() - day_number) % 7
            if difference == 0:
                difference = 7
            return (today - timedelta(days=difference)).strftime('%d/%m/%Y')

    date_match = re.search(
        r'(?<!\d)\d{1,2}[/-]\d{1,2}[/-]\d{2,4}(?!\d)',
        sample_text
    )

    if date_match:
        return parse_date_string(date_match.group())

    return None


def extract_date_range(sample_text):
    date_pattern = r'(?<!\d)\d{1,2}[/-]\d{1,2}[/-]\d{2,4}(?!\d)'
    date_values = re.findall(date_pattern, sample_text)

    if len(date_values) >= 2:
        from_date = parse_date_string(date_values[0])
        to_date = parse_date_string(date_values[1])
        return from_date, to_date

    return None, None


def _http_get(url, params):
    kwargs = {"params": params, "timeout": (15, 60)}
    if USE_CURL_CFFI:
        kwargs["impersonate"] = "chrome"
    return http_requests.get(url, **kwargs)


def _http_post(url, payload, headers):
    kwargs = {"json": payload, "headers": headers, "timeout": (15, 60)}
    if USE_CURL_CFFI:
        kwargs["impersonate"] = "chrome"
    return http_requests.post(url, **kwargs)


def call_api(url, params):
    """Read all Oracle ORDS pages and return their records."""
    rows = []
    offset = 0
    page_size = 100
    for _ in range(100):
        response = _http_get(url, {**params, "limit": page_size, "offset": offset})
        print("Status Code:", response.status_code, flush=True)
        print("Response URL:", response.url, flush=True)
        response.raise_for_status()
        try:
            data = response.json()
        except ValueError as exc:
            raise ValueError(f"Oracle APEX returned non-JSON data: {response.text[:300]}") from exc
        if isinstance(data, list):
            page_rows, has_more = data, False
        elif isinstance(data, dict):
            page_rows = data.get("items", data.get("data", data.get("results", [])))
            has_more = bool(data.get("hasMore", False))
        else:
            raise ValueError("Unexpected Oracle APEX response format.")
        if not isinstance(page_rows, list):
            raise ValueError("Oracle APEX response records are not a list.")
        rows.extend(page_rows)
        if not has_more:
            break
        offset += int((data.get("limit") if isinstance(data, dict) else None) or page_size)
    else:
        raise RuntimeError("Pagination stopped after 100 pages.")
    return pd.DataFrame(rows)

def call_post_api(url, payload):
    headers = {"Content-Type": "application/json"}

    response = _http_post(url, payload, headers)

    print("Status Code:", response.status_code)
    print("Response URL:", response.url)

    if response.status_code >= 400:
        print("Server Error Response:", response.text)

    response.raise_for_status()

    try:
        return response.json()
    except ValueError:
        return response.text


def add_expense(persons, expense_date, description, amount,
                paid_by, expense_type, sub_type, created_by):

    url = os.getenv("APEX_ADD_URL", "https://oracleapex.com/ords/app_exp/add_exp/newexp")

    payload = {
        "P2_FOR_PERSONS": persons,
        "P2_EXPENSE_DATE": expense_date,
        "P2_DESCRIPTION": description,
        "P2_AMOUNT": amount,
        "P2_PAID_BY": paid_by,
        "P2_EXPENSE_TYPE": expense_type,
        "P2_SUB_TYPE": sub_type,
        "P2_CREATED_BY": created_by
    }

    try:
        print("\nAPI: Sending POST request...", flush=True)
        data = call_post_api(url, payload)
        print("API: Response received!", flush=True)
        print("Bot: Expense submission response")
        print(data)
        return data

    except Exception as error:
        print("API Error:", type(error).__name__, error)
        return None


def get_exp_dtls_bsd_on_date(expense_date):
    url = os.getenv("APEX_EXPENSES_URL", "https://oracleapex.com/ords/app_exp/gt/expenses")
    params = {"exp_date": expense_date}

    try:
        print("API: Sending request...", flush=True)
        df = call_api(url, params)
        print("API: Response received!", flush=True)
        print("\nBot: Expense Details")
        print(df)
        return df

    except Exception as error:
        print("API Error:", type(error).__name__, error)
        return None


def get_exp_dtls_bsd_frm_and_to(st_date, ed_date):
    url = os.getenv("APEX_DATE_RANGE_URL", "https://oracleapex.com/ords/app_exp/frmto/exp/dates")
    params = {
        "st_date": st_date,
        "ed_date": ed_date
    }

    try:
        print("API: Sending date-range request...", flush=True)
        df = call_api(url, params)
        print("\nBot: Expense Details")
        print(df)
        return df

    except Exception as error:
        print("API Error:", type(error).__name__, error)
        return None


# =====================================================================
#  WEB API LAYER (new) - replaces run_chatbot(); calls the same functions
#  in the same order. The browser holds the "pending" text between turns,
#  which replaces the original `while missing_values:` input() loop.
# =====================================================================

app = FastAPI(title="Expense Assistant API")

allowed = os.getenv("ALLOWED_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allowed.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    pending_text: Optional[str] = None


def df_to_records(df):
    """DataFrame -> JSON-safe list of dicts (NaN becomes null)."""
    return df.astype(object).where(df.notna(), None).to_dict(orient="records")


def reply(**kwargs):
    base = {
        "intent": None,
        "confidence": None,
        "text": "",
        "payload": None,
        "missing": [],
        "rows": None,
        "response": None,
        "error": None,
        "pending_text": None,
    }
    base.update(kwargs)
    return base


def submit_expense(extracted_data):
    return add_expense(
        extracted_data["P2_FOR_PERSONS"],
        extracted_data["P2_EXPENSE_DATE"],
        extracted_data["P2_DESCRIPTION"],
        extracted_data["P2_AMOUNT"],
        extracted_data["P2_PAID_BY"],
        extracted_data["P2_EXPENSE_TYPE"],
        extracted_data["P2_SUB_TYPE"],
        extracted_data["P2_CREATED_BY"]
    )


def finish_add(extracted_data, missing_values, sample_text, **meta):
    if missing_values:
        return reply(
            text="I could not identify all required details.",
            payload=extracted_data,
            missing=missing_values,
            pending_text=sample_text,
            **meta
        )

    data = submit_expense(extracted_data)
    if data is None:
        return reply(
            text="All details identified, but the expense could not be submitted.",
            payload=extracted_data,
            error="API Error - expense could not be submitted.",
            **meta
        )
    return reply(
        text="All details identified. Expense submitted.",
        payload=extracted_data,
        response=data,
        **meta
    )


@app.get("/")
def home():
    return {"service": "Expense Assistant API", "status": "running", "health": "/api/health"}


@app.get("/health")
@app.get("/api/health")
def health():
    return {"status": "ok", "service": "expense-assistant"}


@app.get("/api/expenses")
def expenses(exp_date: str = None, date_value: str = None):
    """Direct records test endpoint: /api/expenses?exp_date=DD/MM/YYYY"""
    requested_date = exp_date or date_value
    if not requested_date:
        return {"error": "Missing exp_date parameter", "example": "/api/expenses?exp_date=08/11/2026"}
    normalized = parse_date_string(requested_date)
    if not normalized:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid date. Use DD/MM/YYYY.")
    df = get_exp_dtls_bsd_on_date(normalized)
    if df is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=502, detail="Oracle APEX expense API request failed. Check Render logs.")
    return {"count": len(df), "items": df_to_records(df)}


@app.post("/api/chat")
def chat(req: ChatRequest):
    sample_text = req.message.strip()

    if not sample_text:
        return reply(text="Please enter a query.")

    # Continuing an incomplete ADD_EXPENSE:
    # original: sample_text = sample_text + " " + user_input; re-extract
    if req.pending_text:
        sample_text = req.pending_text + " " + sample_text
        extracted_data, missing_values = word_extraction(sample_text)
        return finish_add(extracted_data, missing_values, sample_text,
                          intent="ADD_EXPENSE", confidence=None)

    predicted_intent, confidence = predict_intent(sample_text)
    print("Predicted intent:", predicted_intent)
    print("Confidence:", round(float(confidence), 3))
    meta = {"intent": predicted_intent, "confidence": round(float(confidence), 3)}

    # GET EXPENSE FOR ONE DATE
    if predicted_intent == "GET_EXPENSE":
        expense_date = extract_date(sample_text)

        if expense_date:
            df = get_exp_dtls_bsd_on_date(expense_date)
            if df is None:
                return reply(text=f"Getting expense for {expense_date}",
                             error="API Error - could not fetch expenses.", **meta)
            return reply(text=f"Found {len(df)} expense record(s) for {expense_date}.",
                         rows=df_to_records(df), **meta)
        return reply(text="Please enter a date such as today, yesterday or 03/11/2026.", **meta)

    # ADD EXPENSE USING AUTOMATIC EXTRACTION & MISSING FIELD HANDLING
    elif predicted_intent == "ADD_EXPENSE":
        extracted_data, missing_values = word_extraction(sample_text)
        return finish_add(extracted_data, missing_values, sample_text, **meta)

    # GET EXPENSE BETWEEN TWO DATES
    elif predicted_intent == "GET_DATE_RANGE":
        from_date, to_date = extract_date_range(sample_text)

        if from_date and to_date:
            df = get_exp_dtls_bsd_frm_and_to(from_date, to_date)
            text = f"Found {len(df) if df is not None else 0} expense record(s) from {from_date} to {to_date}."
            if df is None:
                return reply(text=text, error="API Error - could not fetch expenses.", **meta)
            return reply(text=text, rows=df_to_records(df), **meta)
        return reply(text="Please enter both dates in DD/MM/YYYY format.", **meta)

    elif predicted_intent == "GET_PERSON_EXPENSE":
        return reply(text="Person-wise expense API is not connected yet.", **meta)

    elif predicted_intent == "GET_CARD_EXPENSE":
        return reply(text="Card expense API is not connected yet.", **meta)

    elif predicted_intent == "EXPENSE_ANALYSIS":
        return reply(text="Expense analysis is not connected yet.", **meta)

    return reply(text="Sorry, I don't understand. Please try another expense query.", **meta)
