# HB-CTB frontend

The React dashboard shows quote snapshots already saved in MongoDB. Sign-in is handled by FastAPI sessions; the browser never receives MongoDB or FMP credentials. The dashboard reads saved records and does not fetch fresh market data from FMP.

## Start the app

Start the FastAPI backend from the repository root first:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Then, from `frontend/`, install dependencies once and start Vite:

```powershell
npm.cmd install
npm.cmd run dev
```

Open the URL printed by Vite. Its development proxy forwards `/auth` and `/quotes` to `http://127.0.0.1:8000`.

Account creation is invite-only. An administrator issues a one-time code with `python -m app.create_invite`; the developer uses it on the sign-in page to create their own password.

For remote access, deploy the repository with the root `render.yaml` Blueprint. FastAPI serves the built frontend and API from one HTTPS origin; MongoDB and FMP credentials are configured as host environment secrets, never in the browser.
# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and Oxlint's TypeScript related rules in your project.
