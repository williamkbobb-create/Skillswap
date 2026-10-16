-- REVIEW-ONLY Phase 1A migration. Do not apply to production without separate approval.
-- Confirm no external client, workflow, or manual process depends on public.users first.
-- The Flask application uses Supabase Auth and this repository has no public.users queries.
-- RLS alone does not restrict TRUNCATE; these grants are excessive for this app's current flow.
BEGIN;

DROP POLICY IF EXISTS "Allow SkillSwap signup" ON public.users;
DROP POLICY IF EXISTS "Allow skillswap signup" ON public.users;

REVOKE ALL PRIVILEGES ON TABLE public.users FROM anon, authenticated;

COMMIT;
