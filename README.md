# Expense Assistant

- `backend/` — FastAPI service and Oracle APEX integration.
- `frontend/` — static browser chat UI.
- `netlify.toml` — publishes `frontend/` and proxies `/api/*` to Render.

## Run locally

```bash
cd backend
python -m pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open `frontend/index.html`; local requests use `http://localhost:8000`.

## Render deployment

Create a Render **Web Service** from this repository:

- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

After deployment, test `/` and `/api/health` on the exact Render URL. Test records directly with `/api/expenses?exp_date=08/11/2026`.

## Netlify deployment

Import the repository into Netlify. The publish directory is `frontend` from `netlify.toml`.

**Critical:** update the `to` hostname in `netlify.toml` to the exact Render service hostname shown in your Render dashboard. Never use the Netlify site URL as the proxy destination.

## Oracle APEX endpoints

Defaults preserve the existing endpoints. You can override them in Render environment variables:

- `APEX_EXPENSES_URL`
- `APEX_DATE_RANGE_URL`
- `APEX_ADD_URL`

`ALLOWED_ORIGINS` is optional because the deployed frontend calls the API through Netlify's same-origin proxy.

If `/api/health` works but `/api/expenses?exp_date=...` fails, inspect Render logs and verify the Oracle APEX URL, `exp_date` parameter, date format, and ORDS pagination response.
