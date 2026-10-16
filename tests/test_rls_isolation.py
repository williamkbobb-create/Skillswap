"""Opt-in RLS/privilege integration test for a dedicated isolated Supabase project.

Do not run against production. It checks only that client roles cannot query the
legacy public.users table after the review migration has been deliberately applied.
"""
import os

import pytest
from supabase import create_client


@pytest.mark.integration
def test_authenticated_test_users_cannot_query_legacy_public_users():
    if os.getenv("SKILLSWAP_TEST_ENV") != "isolated":
        pytest.skip("Use SKILLSWAP_TEST_ENV=isolated only for a dedicated test project")
    url = os.getenv("SKILLSWAP_TEST_SUPABASE_URL", "")
    key = os.getenv("SKILLSWAP_TEST_SUPABASE_KEY", "")
    accounts = [
        (os.getenv("SKILLSWAP_TEST_USER_A_EMAIL", ""), os.getenv("SKILLSWAP_TEST_USER_A_PASSWORD", "")),
        (os.getenv("SKILLSWAP_TEST_USER_B_EMAIL", ""), os.getenv("SKILLSWAP_TEST_USER_B_PASSWORD", "")),
    ]
    if not url or not key or not all(email and password for email, password in accounts):
        pytest.skip("Dedicated test-project credentials and two test accounts are required")
    if "wysmsredwgfiigvnqzut" in url:
        pytest.fail("Refusing to run this integration test against the production SkillSwap project")

    for email, password in accounts:
        client = create_client(url, key)
        client.auth.sign_in_with_password({"email": email, "password": password})
        # No rows are fetched; expected behavior is a permission error after migration.
        with pytest.raises(Exception):
            client.table("users").select("id").limit(1).execute()
