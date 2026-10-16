# Phase 1A rollback and deployment notes

## Application rollback
If this patch causes a regression, revert the Phase 1A commit or redeploy the previously known-good commit on the existing deployment branch. This branch must not be deployed during this phase.

## Database migration
The migration in `supabase/migrations/` is a proposal only and must not be run against production without separate approval. Before applying it anywhere, verify that no external app, workflow, or manual process depends on direct access to `public.users`.

If the migration is applied to an isolated test database and needs rollback, restore the audited pre-migration grants and policies only in that test database:

```sql
GRANT ALL PRIVILEGES ON TABLE public.users TO anon, authenticated;
CREATE POLICY "Allow SkillSwap signup" ON public.users FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "Allow skillswap signup" ON public.users FOR INSERT TO anon WITH CHECK (true);
```

This restores the previously observed grants and policies, including the excessive privileges and duplicate policy. It is recovery guidance, not a recommended steady state.

## Configuration
The app requires `FLASK_SECRET_KEY`. The existing `render.yaml` already generates this value; this patch does not change Render configuration. For local HTTP development only, set `SESSION_COOKIE_SECURE=false`; keep it enabled in production HTTPS.

## Tests
Install development dependencies with `pip install -r requirements-dev.txt`, then run `pytest -q`. RLS integration tests must use a dedicated isolated Supabase project and test accounts, never production credentials.
