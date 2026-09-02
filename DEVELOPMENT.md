# UniTrack Development Guide

This document records the local commands and environment variables used by the
backend and frontend, plus the quality gates introduced in Milestone 1.

> Never commit the backend `.env`, frontend `.env`, local databases, or test
> output. These are covered by the repository `.gitignore`.

## Repository layout

- `unitrack-backend/` — Django 5.2 + Django REST Framework (JWT auth), venv at `unitrack-backend/venv`.
- `unitrack-frontend/` — React 19 + TypeScript + Vite (Vitest for tests).

## Backend

### Setup

1. Create the virtual environment (if not present): `python -m venv venv`
2. Activate it and install dependencies: `pip install -r requirements.txt`
3. Create `.env` in `unitrack-backend/` with the variables below.
4. Apply migrations: `python manage.py migrate`

### Env vars (keys only — values are secrets)

| Variable | Purpose |
|---|---|
| `DEBUG` | `True` in development |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary account name |
| `CLOUDINARY_API_KEY` | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` / `ADMIN_FULL_NAME` | Seed admin credentials |

### Run

- Run tests: `python manage.py test`
- Run a single test module: `python manage.py test accounts.tests`
- System check: `python manage.py check`
- Start server: `python manage.py runserver`

Tests use `force_authenticate` against reusable factories in
`accounts/factories.py` and `projects/factories.py`. SQLite runs tests against
an in-memory database for speed; Postgres/other engines are unaffected.

## Frontend

### Setup

1. `npm install`
2. Create `.env` (or `.env.local`) with `VITE_API_URL` set to the backend base
   URL (e.g. `http://127.0.0.1:8000`).

### Run

- Dev server: `npm run dev`
- Tests (once): `npm test`
- Tests (watch): `npm run test:watch`
- Coverage: `npm run test:coverage`
- Lint: `npm run lint`
- Production build (also type-checks): `npm run build`

Tests run under Vitest with jsdom and are configured in `vite.config.ts`
(`test` block). Shared DOM helpers live in `src/test/`; the Axios client is
mocked with `axios-mock-adapter` in `src/lib/__tests__/api.test.ts`.

## Quality gates

Run all of the following before considering a milestone complete:

1. Backend: `python manage.py test` (from `unitrack-backend`)
2. Frontend: `npm test`
3. Frontend lint: `npm run lint`
4. Frontend build: `npm run build`

A convenience script runs all four gates together:

- PowerShell: `scripts/run-all-checks.ps1`

## Authentication notes

- The DRF API authenticates via HttpOnly cookies and a local-storage bearer
  token. The frontend `src/lib/api.ts` attaches the token and transparently
  refreshes once on `401`.
- Dashboard routes are guarded by `RequireRole` (`src/components/require-role.tsx`);
  requests themselves are authorized server-side by DRF permission classes.