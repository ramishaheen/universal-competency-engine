from __future__ import annotations


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_login_with_bootstrap_admin(client):
    r = client.post(
        "/auth/login",
        data={"username": "admin@example.com", "password": "adminpass123"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_register_creates_operator(client):
    r = client.post(
        "/auth/register",
        json={"email": "u1@example.com", "password": "pass1234", "full_name": "U One"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["email"] == "u1@example.com"
    assert "operator" in body["roles"]


def test_create_and_get_competency(client, admin_headers, sample_definition):
    r = client.post("/competencies", json={"definition": sample_definition}, headers=admin_headers)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["id"] == "demo"
    assert body["definition"]["name"] == "Demo Competency"

    r = client.get("/competencies", headers=admin_headers)
    assert r.status_code == 200
    assert any(c["id"] == "demo" for c in r.json())

    r = client.get("/competencies/demo", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["domain"] == ""


def test_validate_endpoint_rejects_bad_definition(client, admin_headers):
    bad = {"id": "x", "name": ""}  # missing things, but name is empty; bad ref via workflow
    r = client.post("/competencies/validate", json={"definition": bad}, headers=admin_headers)
    # Empty name is technically valid per schema; let's send something semantically broken instead
    semantically_broken = {
        "id": "bad",
        "name": "Bad",
        "workflows": [
            {"id": "w", "name": "W", "steps": [{"id": "r", "type": "skill", "skill": "ghost"}]}
        ],
    }
    r = client.post(
        "/competencies/validate", json={"definition": semantically_broken}, headers=admin_headers
    )
    assert r.status_code == 400


def test_execute_succeeds_with_stub_llm(client, admin_headers, sample_definition):
    client.post("/competencies", json={"definition": sample_definition}, headers=admin_headers)
    r = client.post(
        "/competencies/demo/execute",
        json={"inputs": {"text": "hello"}, "run_plan": False},
        headers=admin_headers,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "succeeded"
    assert "stub-reply" in body["outputs"]["msg"]


def test_audit_log_populated(client, admin_headers, sample_definition):
    client.post("/competencies", json={"definition": sample_definition}, headers=admin_headers)
    client.post(
        "/competencies/demo/execute",
        json={"inputs": {"text": "hi"}, "run_plan": False},
        headers=admin_headers,
    )
    r = client.get("/audit?competency_id=demo", headers=admin_headers)
    assert r.status_code == 200
    events = r.json()
    assert any(e["event_type"] == "run.start" for e in events)
    assert any(e["event_type"] == "run.end" for e in events)


def test_memory_endpoints(client, admin_headers, sample_definition):
    client.post("/competencies", json={"definition": sample_definition}, headers=admin_headers)
    r = client.post(
        "/competencies/demo/memory",
        json={"type": "semantic", "content": "users prefer concise output", "importance": 0.8},
        headers=admin_headers,
    )
    assert r.status_code == 201, r.text
    entry_id = r.json()["id"]

    r = client.get("/competencies/demo/memory", headers=admin_headers)
    assert r.status_code == 200
    assert len(r.json()) == 1

    r = client.delete(f"/competencies/demo/memory/{entry_id}", headers=admin_headers)
    assert r.status_code == 200


def test_performance_endpoint(client, admin_headers, sample_definition):
    client.post("/competencies", json={"definition": sample_definition}, headers=admin_headers)
    for _ in range(3):
        client.post(
            "/competencies/demo/execute",
            json={"inputs": {"text": "x"}, "run_plan": False},
            headers=admin_headers,
        )
    r = client.get("/competencies/demo/performance", headers=admin_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["runs"] == 3
    assert body["success_rate"] == 1.0


def test_unauthenticated_request_rejected(client):
    r = client.get("/competencies")
    assert r.status_code == 401


def test_role_protection_blocks_operator_from_writing(client, admin_headers, sample_definition):
    # Register a non-admin user
    client.post(
        "/auth/register",
        json={"email": "op@example.com", "password": "pass1234"},
    )
    r = client.post("/auth/login", data={"username": "op@example.com", "password": "pass1234"})
    op_token = r.json()["access_token"]
    op_headers = {"Authorization": f"Bearer {op_token}"}

    # Operator may NOT create
    r = client.post("/competencies", json={"definition": sample_definition}, headers=op_headers)
    assert r.status_code == 403

    # But operator may execute one the admin made
    client.post("/competencies", json={"definition": sample_definition}, headers=admin_headers)
    r = client.post(
        "/competencies/demo/execute",
        json={"inputs": {"text": "ok"}, "run_plan": False},
        headers=op_headers,
    )
    assert r.status_code == 201, r.text
