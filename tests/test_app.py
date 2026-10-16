import os
import re
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

os.environ.setdefault("FLASK_SECRET_KEY", "test-only-secret-not-for-production")
os.environ.setdefault("SESSION_COOKIE_SECURE", "false")
os.environ.pop("SUPABASE_URL", None)
os.environ.pop("SUPABASE_KEY", None)

import app as skillswap


class FakeAuth:
    def __init__(self):
        self.sign_up = Mock(side_effect=self._signup)
        self.sign_in_with_password = Mock(side_effect=self._login)
        self.error = None
        self.user = SimpleNamespace(
            id="auth-user-a",
            email="learner@example.test",
            user_metadata={
                "full_name": "Test Learner",
                "skills_to_teach": ["Python programming"],
                "skills_to_learn": ["Data analysis"],
            },
        )

    def _signup(self, payload):
        if self.error:
            raise self.error
        return SimpleNamespace(user=self.user, session=object())

    def _login(self, payload):
        if self.error:
            raise self.error
        return SimpleNamespace(user=self.user, session=object())


class FakeSupabase:
    def __init__(self, auth):
        self.auth = auth
        self.table = Mock(side_effect=AssertionError("Flask app must not query public.users"))


@pytest.fixture
def setup_client(monkeypatch):
    skillswap.app.config.update(TESTING=True, WTF_CSRF_ENABLED=True, SESSION_COOKIE_SECURE=False)
    auth = FakeAuth()
    supabase = FakeSupabase(auth)
    monkeypatch.setattr(skillswap, "supabase", supabase)
    return skillswap.app.test_client(), auth, supabase


def token_for(client, path="/signup"):
    response = client.get(path)
    assert response.status_code == 200
    found = re.search(rb'name="csrf_token" value="([^"]+)"', response.data)
    assert found
    return found.group(1).decode()


def form(token, **overrides):
    data = {
        "csrf_token": token,
        "name": "Test Learner",
        "email": "Learner@Example.test",
        "password": "strong-test-password",
        "skills_to_teach": ["Python programming"],
        "skills_to_learn": ["Data analysis"],
    }
    data.update(overrides)
    return data


def test_signup_success_uses_supabase_auth_and_allowlisted_skills(setup_client):
    client, auth, supabase = setup_client
    response = client.post("/signup", data=form(token_for(client)), follow_redirects=True)
    assert response.status_code == 200
    assert b"Account created with your skills saved" in response.data
    auth.sign_up.assert_called_once()
    payload = auth.sign_up.call_args.args[0]
    assert payload["email"] == "learner@example.test"
    assert payload["options"]["data"]["skills_to_teach"] == ["Python programming"]
    with client.session_transaction() as sess:
        assert sess["user"]["id"] == "auth-user-a"
    supabase.table.assert_not_called()


def test_duplicate_email_uses_generic_error(setup_client):
    client, auth, _ = setup_client
    auth.error = RuntimeError("duplicate learner@example.test internal-provider-detail")
    response = client.post("/signup", data=form(token_for(client)), follow_redirects=True)
    assert response.status_code == 200
    assert b"may already be registered" in response.data
    assert b"internal-provider-detail" not in response.data


@pytest.mark.parametrize("overrides", [
    {"email": "not-an-email"}, {"password": "short"}, {"name": ""},
    {"skills_to_teach": []}, {"skills_to_learn": []},
    {"skills_to_teach": ["unapproved skill"]},
])
def test_invalid_signup_rejected_before_auth(setup_client, overrides):
    client, auth, _ = setup_client
    response = client.post("/signup", data=form(token_for(client), **overrides), follow_redirects=True)
    assert response.status_code == 200
    auth.sign_up.assert_not_called()


def test_missing_csrf_token_rejected(setup_client):
    client, auth, _ = setup_client
    response = client.post("/signup", data=form(""))
    assert response.status_code == 400
    auth.sign_up.assert_not_called()


def test_missing_supabase_configuration_fails_closed(monkeypatch):
    monkeypatch.setattr(skillswap, "supabase", None)
    client = skillswap.app.test_client()
    response = client.post("/signup", data=form(token_for(client)), follow_redirects=True)
    assert response.status_code == 200
    assert b"Account services are not configured" in response.data


def test_login_uses_auth_identity_not_submitted_user_id(setup_client):
    client, auth, supabase = setup_client
    response = client.post("/login", data={
        "csrf_token": token_for(client, "/login"),
        "email": "learner@example.test",
        "password": "strong-test-password",
        "user_id": "spoofed-user-id",
    }, follow_redirects=True)
    assert response.status_code == 200
    with client.session_transaction() as sess:
        assert sess["user"]["id"] == "auth-user-a"
    supabase.table.assert_not_called()


def test_missing_flask_secret_fails_startup():
    env = os.environ.copy()
    env.pop("FLASK_SECRET_KEY", None)
    env.pop("SUPABASE_URL", None)
    env.pop("SUPABASE_KEY", None)
    result = subprocess.run(
        [sys.executable, "-c", "import app"], env=env, capture_output=True,
        text=True, timeout=15,
    )
    assert result.returncode != 0
    assert "FLASK_SECRET_KEY must be set" in result.stderr
