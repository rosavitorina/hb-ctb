# HB-CTB

HB-CTB collects market quotes from Financial Modeling Prep (FMP), saves them in MongoDB, and displays saved snapshots in a React carousel.

## Current data flow

1. A quote collection request fetches a symbol from FMP.
2. The response is saved to `integracao_db.respostas_api` in MongoDB.
3. The React app reads saved documents from FastAPI and displays them. Opening or refreshing the dashboard does not call FMP.

## Configure

Use Python and Node.js, then create a local environment file from the tracked template:

```powershell
Copy-Item .env.example .env
```

Set `MONGO_URI` in `.env` to read accounts and saved quotes from MongoDB. `FMP_API_KEY` is only needed when fetching new quotes; opening the dashboard reads existing MongoDB records and does not spend FMP quota. Keep real credentials private; `.env` is ignored by Git and excluded from the deployment image.

## Run locally

Install backend dependencies from the repository root:

```powershell
python -m pip install -r requirements.txt
```

Start FastAPI in one terminal from the repository root:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Install and start React in another terminal:

```powershell
cd .\frontend
npm.cmd install
npm.cmd run dev
```

Open the local URL Vite prints, usually `http://localhost:5173/`. The Vite development server proxies `/quotes` to FastAPI on port 8000.

## Accounts

An administrator can issue an email-bound, one-time invite from the repository root:

```powershell
python -m app.create_invite
```

Enter the developer's email. The CLI prints a random invite code once; share it privately with that developer. It expires after 72 hours, can only be redeemed once, and is bound to that email. The invited developer selects “Have an invite? Create account” on the sign-in page and sets their own password (at least 12 characters). Registration immediately signs them in. The database stores only the invite-code hash and a scrypt password hash. Users share the saved quote feed in this initial version.

Administrators can still directly provision an account locally with `python -m app.create_user` when needed.

To rotate an account password and revoke its active sessions, run:

```powershell
python -m app.reset_password
```

Login and invite registration are rate-limited in the single app process. If running multiple instances, move the limiter to shared storage such as Redis. Add account recovery/administration controls before treating this as a production identity system.

## Deploy for remote teammates

The repository includes a Render Blueprint and Docker build for a single HTTPS web service. Push the project to GitHub, then in Render create a new Blueprint and connect this repository. Render reads `render.yaml` and asks you to provide `MONGO_URI` and `FMP_API_KEY` as service secrets. Do not add either value to this repository. `AUTH_COOKIE_SECURE=true` is configured for HTTPS cookies.

Before deployment succeeds, allow the Render service's outbound IP addresses in MongoDB Atlas Network Access. Keep the database user restricted to the required database and permissions; avoid opening Atlas to all IPs if your hosting plan provides specific outbound addresses.

After deployment, use the HTTPS URL Render provides. To invite a teammate, run `python -m app.create_invite` locally with the same MongoDB URI in your ignored `.env`, then share the email-bound code privately. The teammate creates their own password on the hosted sign-in page. The browser never connects directly to MongoDB or receives the FMP key.

## API

- `GET /health` checks that FastAPI is running.
- `POST /auth/login`, `POST /auth/register`, `GET /auth/me`, and `POST /auth/logout` manage sign-in. Registration requires an email-matched active invite.
- Login and registration are limited per client address to slow automated attempts.
- `GET /quotes?limit=100` reads up to 100 saved MongoDB documents and requires a session. It does not contact FMP.
- `POST /quotes/{symbol}` fetches a new quote from FMP, saves it to MongoDB, and requires a session. This uses the FMP API.

## Tests

Run the Mongo quote retrieval unit tests from the repository root:

```powershell
python -m unittest discover -s tests/unit
```
pip install -r requirements.txt