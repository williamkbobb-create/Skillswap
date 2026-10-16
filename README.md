# SkillSwap

A responsive Flask starter application for a community where people can share skills and learn from one another. Includes a landing page, signup, login, logout, Supabase Auth integration, and a Render deployment blueprint.

## Stack

- Python + Flask
- Supabase Auth
- Flask-WTF CSRF protection
- Gunicorn
- Responsive HTML/CSS

## Run locally

1. Use Python 3.12 or newer.
2. Create and activate a virtual environment.
3. Install development dependencies: `pip install -r requirements-dev.txt`
4. Set the environment variables below.
5. Start the app: `python app.py`

Required environment variables:

- `FLASK_SECRET_KEY`: a long, random secret value. The app refuses to start if it is missing.
- `SUPABASE_URL`: your Supabase project URL.
- `SUPABASE_KEY`: your Supabase publishable key (or legacy anon key). Never use a service-role/secret key in a browser or commit it to GitHub.
- `SESSION_COOKIE_SECURE`: defaults to `true`; set to `false` only for local HTTP development/testing.

The health endpoint is `/health`. It reports whether Supabase configuration is present; it does not test authentication credentials.

## Deploy to Render

Create a Python web service connected to this repository and the `main` branch. Render can use the included `render.yaml`, or configure:

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Health check path: `/health`

Add `SUPABASE_URL` and `SUPABASE_KEY` in the Render service's Environment settings. Generate a secure `FLASK_SECRET_KEY`; do not commit real values. If email confirmation is enabled in Supabase, users may need to confirm their email before logging in.

## Tests

Run unit tests with `pytest -q`. The optional RLS integration test is skipped unless a dedicated isolated Supabase project and two pre-created test accounts are configured. Never use production credentials for integration tests.

## Phase 1A security note

Signup and login use Supabase Auth; this repository contains no code that queries `public.users`. The migration under `supabase/migrations/` is a proposal only and must not be applied to production until external consumers are ruled out and separate approval is granted. See `docs/security/phase-1a-rollback.md`.

## Current scope

This is the initial foundation, not a complete skill marketplace yet. Skill listings, search/matching, user profiles, messaging, and moderation still need to be implemented before the product is ready for public use.