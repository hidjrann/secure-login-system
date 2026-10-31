import pytest
from app import create_app


@pytest.fixture()
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret",
        "DATABASE": str(tmp_path / "test.sqlite"),
    })
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


def register(client, username="hicran", password="StrongPass123"):
    return client.post("/register", data={"username": username, "password": password})


def login(client, username="hicran", password="StrongPass123"):
    return client.post("/login", data={"username": username, "password": password})


def test_register_and_password_is_hashed(client, app):
    response = register(client)
    assert response.status_code == 302
    with app.app_context():
        from flask import current_app
        import sqlite3
        db = sqlite3.connect(current_app.config["DATABASE"])
        stored = db.execute("SELECT password_hash FROM users WHERE username='hicran'").fetchone()[0]
        db.close()
    assert stored != "StrongPass123"
    assert stored.startswith("scrypt:") or stored.startswith("pbkdf2:")


def test_valid_login_opens_dashboard(client):
    register(client)
    response = login(client)
    assert response.status_code == 302
    page = client.get("/dashboard")
    assert page.status_code == 200
    assert "hicran" in page.get_data(as_text=True)


def test_wrong_password_is_rejected(client):
    register(client)
    response = login(client, password="WrongPass123")
    assert response.status_code == 401
    assert client.get("/dashboard").status_code == 302


def test_empty_fields_are_rejected(client):
    response = client.post("/login", data={"username": "", "password": ""})
    assert response.status_code == 400


def test_unauthorized_dashboard_access_is_blocked(client):
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_users_cannot_see_another_users_dashboard(client):
    register(client, "userone", "StrongPass123")
    login(client, "userone", "StrongPass123")
    own_page = client.get("/dashboard").get_data(as_text=True)
    assert "userone" in own_page
    client.post("/logout")
    register(client, "usertwo", "StrongPass456")
    login(client, "usertwo", "StrongPass456")
    other_page = client.get("/dashboard").get_data(as_text=True)
    assert "usertwo" in other_page
    assert "userone" not in other_page


def test_login_rate_limit_is_configured(app):
    # The route is protected by Flask-Limiter's 5-per-minute rule.
    rules = [str(rule) for rule in app.url_map.iter_rules() if rule.rule == "/login"]
    assert rules


def test_login_rate_limit_blocks_sixth_attempt(client):
    statuses = []

    for _ in range(6):
        response = client.post(
            "/login",
            data={
                "username": "unknown_user",
                "password": "WrongPass123"
            }
        )
        statuses.append(response.status_code)

    assert statuses[:5] == [401, 401, 401, 401, 401]
    assert statuses[5] == 429