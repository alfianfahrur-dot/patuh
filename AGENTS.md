# PATUH — Base44 Dev Environment

## Stack
- **Backend**: Python FastAPI (uvicorn, MongoDB via motor) on port 8000
- **Frontend**: React 19 + Create React App (craco, Tailwind, Radix UI) on port 3000
- **Database**: MongoDB 7

## Setup
```
docker compose -f docker-compose.base44.yml up -d --build
```

## Key env vars
- `MONGO_URL`, `DB_NAME` — MongoDB connection (set in compose, local)
- `JWT_SECRET` — JWT signing (generated dev placeholder; user should replace)
- `REACT_APP_BACKEND_URL` — public URL of backend API, passed to frontend
- `EMERGENT_EMAIL_KEY` — external email service (optional for boot)
- `EMERGENT_LLM_KEY` — external file storage (optional for boot)

## Admin login
- Email: `admin@example.com`
- Password: `admin123`

## Notes
- `litellm` is in requirements.txt but not imported; filtered out during Docker build to avoid private URL fetch failure.
- `@emergentbase/overlay` disabled via `DISABLE_EMERGENT_OVERLAY=true` to avoid loading issues in sandbox.
- File watching uses polling (`CHOKIDAR_USEPOLLING`, `WATCHFILES_FORCE_POLLING`) for bind-mount compatibility.
- No yarn.lock exists; `yarn install` (without `--frozen-lockfile`) generates one on first run.
