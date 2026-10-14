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

Create a Google OAuth 2.0 Web application client in Google Cloud Console. Add your local and deployed website origins as authorized JavaScript origins, then set the client ID in `.env`. The ID is public; do not add a client secret because Google Identity Services returns an ID token that FastAPI validates server-side.

```env
GOOGLE_CLIENT_ID=your-google-oauth-client-id.apps.googleusercontent.com
```

Add `http://localhost:5173` for local development and `https://hb-t8z4.onrender.com` for the current production site. This sign-in flow does not use an OAuth redirect URI. Set the same `GOOGLE_CLIENT_ID` in Render’s service environment; the frontend reads it at runtime from `/auth/config`, so changing the client ID does not require rebuilding the frontend.

Google Cloud setup:

1. In Google Cloud Console, select or create a project and configure Google Auth Platform branding and audience. Choose **External** if users outside your organization need access. Add test users while the consent screen is in Testing; publish the app before opening it to general users.
2. Create an OAuth client with application type **Web application**.
3. Add these authorized JavaScript origins (no redirect URI is needed):
	- `http://localhost:5173`
	- `https://hb-t8z4.onrender.com`
4. Copy the client ID into local `.env` and the Render web service environment as `GOOGLE_CLIENT_ID`.
5. Deploy the current repository revision and verify `https://hb-t8z4.onrender.com/auth/config` returns the configured client ID before testing sign-in.

Optional legacy email-invite and administrator settings:

```env
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your-smtp-user
SMTP_PASSWORD=your-smtp-password
SMTP_FROM=noreply@example.com
EMAIL_USE_TLS=true
INITIAL_ADMIN_EMAILS=admin1@example.com,admin2@example.com,admin3@example.com
```

The Google OAuth config is required for the sign-in button. The backend validates the Google ID token, checks its audience against `GOOGLE_CLIENT_ID`, and creates or reuses the account using its verified email. Legacy email/password and invite API routes remain for existing installations, but the website does not expose them.

The app sends transactional email only when `SMTP_HOST` is configured. In local development, tests use mocked email delivery and no real mail is sent. The admin bootstrap is safe and idempotent: it promotes only the explicitly configured addresses, normalizes them to lowercase, and never grants privileges to the first registered user or any unlisted address.

To promote the three configured administrators, start the app once with the environment values set and the database reachable. The startup hook runs the bootstrapping process automatically. If you prefer a one-off command, run:

```powershell
python -c "from app.services.auth_service import bootstrap_admins; print(bootstrap_admins())"
```

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

Google sign-in is the account flow. The browser requests a Google identity token, the backend verifies it with Google, and the app creates or reuses the account based on its verified email. If the email matches `INITIAL_ADMIN_EMAILS`, that account is promoted to `admin` automatically. Users can view their email and access role under **My account** and sign out from the sidebar.

Google Identity Services provides sign-in, not website subscription billing. This app currently has no subscription checkout or billing integration. Website subscriptions require a separate billing provider; Google Play Billing is for eligible Android app distribution, not general web checkout.

Google sign-in creates an account on the user’s first successful login. Accounts matching `INITIAL_ADMIN_EMAILS` receive the administrator role only after Google verifies the email. Users can review their email and access role under **My account** and sign out from the sidebar.

## Deploy for remote teammates

The repository includes a Render Blueprint and Docker build for a single HTTPS web service. Push the project to GitHub, then deploy the Blueprint or update the existing service. Configure `MONGO_URI`, `FMP_API_KEY`, and `GOOGLE_CLIENT_ID` in Render’s environment settings. Do not commit secret values. `AUTH_COOKIE_SECURE=true` is configured for HTTPS cookies.

Before deployment succeeds, allow the Render service's outbound IP addresses in MongoDB Atlas Network Access. Keep the database user restricted to the required database and permissions; avoid opening Atlas to all IPs if your hosting plan provides specific outbound addresses.

After deployment, add the exact HTTPS origin to the OAuth client’s authorized JavaScript origins and set `GOOGLE_CLIENT_ID` in Render. The browser never connects directly to MongoDB or receives the FMP key.

## API

- `GET /health` checks that FastAPI is running.
- `GET /auth/config` returns the public Google client ID; `POST /auth/google`, `GET /auth/me`, and `POST /auth/logout` manage Google sign-in sessions.
- Legacy `POST /auth/login` and `POST /auth/register` routes remain for existing account migrations; the website does not expose them.
- Login and registration are limited per client address to slow automated attempts.
- `GET /quotes?limit=100` reads up to 100 saved MongoDB documents and requires a session. It does not contact FMP.
- `POST /quotes/{symbol}` fetches a new quote from FMP, saves it to MongoDB, and requires a session. This uses the FMP API.

## Tests

Run the Mongo quote retrieval unit tests from the repository root:

```powershell
python -m unittest discover -s tests/unit
```
pip install -r requirements.txt