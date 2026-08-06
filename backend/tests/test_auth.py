def test_register_then_login(client):
    resp = client.post(
        "/auth/register", json={"email": "a@example.com", "password": "password123"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "access_token" in body and "refresh_token" in body
    assert body["user"]["email"] == "a@example.com"

    resp = client.post(
        "/auth/login", json={"email": "a@example.com", "password": "password123"}
    )
    assert resp.status_code == 200


def test_register_duplicate_email_returns_409(client):
    client.post("/auth/register", json={"email": "dup@example.com", "password": "password123"})
    resp = client.post(
        "/auth/register", json={"email": "dup@example.com", "password": "password123"}
    )
    assert resp.status_code == 409


def test_login_wrong_password_returns_401(client):
    client.post("/auth/register", json={"email": "b@example.com", "password": "password123"})
    resp = client.post(
        "/auth/login", json={"email": "b@example.com", "password": "wrongpass"}
    )
    assert resp.status_code == 401


def test_register_short_password_returns_422(client):
    # Pydantic's Field(min_length=8) on RegisterRequest catches this before
    # the route body runs -- same "schema catches shape errors" pattern as
    # ComputeRequest's Literal[...] in test_compute.py.
    resp = client.post(
        "/auth/register", json={"email": "c@example.com", "password": "short"}
    )
    assert resp.status_code == 422


def test_refresh_issues_new_access_token(client):
    reg = client.post(
        "/auth/register", json={"email": "d@example.com", "password": "password123"}
    )
    refresh_token = reg.json()["refresh_token"]

    resp = client.post(
        "/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"}
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_refresh_rejects_access_token(client, auth_headers):
    # auth_headers carries an ACCESS token. Using it against /auth/refresh
    # should fail -- this is the "access token type" check in
    # core/security.py's decode_token(expected_type="refresh") doing its job.
    access_token = auth_headers["Authorization"].split(" ")[1]
    resp = client.post(
        "/auth/refresh", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert resp.status_code == 401


def test_me_requires_auth(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 403  # HTTPBearer: no header at all -> 403


def test_me_returns_current_user(client, auth_headers):
    resp = client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "tester@example.com"