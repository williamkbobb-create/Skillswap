import os
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
from supabase import create_client

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-this-before-production")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

SKILL_OPTIONS = [
    "Web development", "Graphic design", "Python programming", "Data analysis",
    "Digital marketing", "Video editing", "Photography", "Writing and content",
    "UI/UX design", "Business and entrepreneurship", "Languages", "Mathematics",
    "Career development", "Microsoft Office", "Mobile app development", "Public speaking",
]


def require_supabase(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if supabase is None:
            flash("Account services are not configured yet. Please try again later.", "error")
            return redirect(url_for("index"))
        return view(*args, **kwargs)
    return wrapped


@app.get("/")
def index():
    return render_template("index.html", user=session.get("user"))


@app.get("/signup")
def signup_page():
    return render_template("signup.html", skill_options=SKILL_OPTIONS)


@app.post("/signup")
@require_supabase
def signup():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    skills_to_teach = [skill for skill in request.form.getlist("skills_to_teach") if skill in SKILL_OPTIONS]
    skills_to_learn = [skill for skill in request.form.getlist("skills_to_learn") if skill in SKILL_OPTIONS]

    if not name or not email or len(password) < 8:
        flash("Enter your name, a valid email, and a password with at least 8 characters.", "error")
        return redirect(url_for("signup_page"))
    if not skills_to_teach:
        flash("Please select at least one skill you can teach.", "error")
        return redirect(url_for("signup_page"))
    if not skills_to_learn:
        flash("Please select at least one skill you want to learn.", "error")
        return redirect(url_for("signup_page"))

    try:
        result = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {
                "full_name": name,
                "skills_to_teach": skills_to_teach,
                "skills_to_learn": skills_to_learn,
            }}
        })
        if result.user:
            if result.session:
                session["user"] = {
                    "id": result.user.id, "email": result.user.email, "name": name,
                    "skills_to_teach": skills_to_teach, "skills_to_learn": skills_to_learn,
                }
            flash("Account created with your skills saved. Check your email if confirmation is required.", "success")
            return redirect(url_for("index"))
        flash("We could not create your account. Please check your details and try again.", "error")
    except Exception as exc:
        app.logger.warning("Signup failed: %s", str(exc))
        flash("We could not create your account. The email may already be registered, or Supabase may need configuration.", "error")
    return redirect(url_for("signup_page"))


@app.get("/login")
def login_page():
    return render_template("login.html")


@app.post("/login")
@require_supabase
def login():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    try:
        result = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if result.user:
            metadata = result.user.user_metadata or {}
            session["user"] = {
                "id": result.user.id,
                "email": result.user.email,
                "name": metadata.get("full_name", result.user.email.split("@")[0]),
                "skills_to_teach": metadata.get("skills_to_teach", []),
                "skills_to_learn": metadata.get("skills_to_learn", []),
            }
            flash("Welcome back!", "success")
            return redirect(url_for("index"))
    except Exception as exc:
        app.logger.warning("Login failed: %s", str(exc))
    flash("Login failed. Check your email and password, then try again.", "error")
    return redirect(url_for("login_page"))


@app.post("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("index"))


@app.get("/health")
def health():
    return {"status": "ok", "supabase_configured": bool(supabase)}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
