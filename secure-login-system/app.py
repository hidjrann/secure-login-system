import os
import sqlite3
from functools import wraps
from pathlib import Path

from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-this-secret"),
        DATABASE=os.environ.get("DATABASE", str(Path(app.instance_path) / "secure_login.sqlite")),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
        PERMANENT_SESSION_LIFETIME=1800,
        WTF_CSRF_TIME_LIMIT=3600,
    )

    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    csrf = CSRFProtect()
    csrf.init_app(app)

    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=[],
        storage_uri="memory://",
    )

    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON")
        return g.db

    @app.teardown_appcontext
    def close_db(exception=None):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    def init_db():
        db = get_db()
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.commit()

    with app.app_context():
        init_db()

    def login_required(view):
        @wraps(view)
        def wrapped_view(**kwargs):
            if session.get("user_id") is None:
                return redirect(url_for("login"))
            return view(**kwargs)
        return wrapped_view

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Content-Security-Policy",
                                    "default-src 'self'; style-src 'self' 'unsafe-inline'")
        return response

    @app.get("/")
    def index():
        if session.get("user_id"):
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))

    @app.route("/register", methods=["GET", "POST"])
    @limiter.limit("10 per minute")
    def register():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")

            if not username or not password:
                flash("Bütün sahələri doldurun.", "error")
                return render_template("register.html"), 400
            if len(username) < 3 or len(username) > 30:
                flash("İstifadəçi adı 3–30 simvol olmalıdır.", "error")
                return render_template("register.html"), 400
            if len(password) < 8:
                flash("Parol ən azı 8 simvol olmalıdır.", "error")
                return render_template("register.html"), 400

            db = get_db()
            try:
                db.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, generate_password_hash(password))
                )
                db.commit()
            except sqlite3.IntegrityError:
                flash("Bu istifadəçi adı artıq mövcuddur.", "error")
                return render_template("register.html"), 409

            flash("Qeydiyyat uğurla tamamlandı. İndi daxil ola bilərsiniz.", "success")
            return redirect(url_for("login"))

        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    @limiter.limit("5 per minute")
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")

            if not username or not password:
                flash("İstifadəçi adı və parol tələb olunur.", "error")
                return render_template("login.html"), 400

            user = get_db().execute(
                "SELECT id, username, password_hash FROM users WHERE username = ?",
                (username,)
            ).fetchone()

            if user is None or not check_password_hash(user["password_hash"], password):
                flash("İstifadəçi adı və ya parol yanlışdır.", "error")
                return render_template("login.html"), 401

            session.clear()
            session.permanent = True
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))

        return render_template("login.html")

    @app.get("/dashboard")
    @login_required
    def dashboard():
        return render_template("dashboard.html", username=session.get("username"))

    @app.post("/logout")
    @login_required
    def logout():
        session.clear()
        flash("Sistemdən təhlükəsiz çıxış etdiniz.", "success")
        return redirect(url_for("login"))

    # Small health endpoint for deployment checks; exposes no user data.
    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()

if __name__ == "__main__":
    # Local development only. For public deployment use a production WSGI server.
    app.run(host="127.0.0.1", port=5000, debug=False)
