import json
import os
import uuid
from datetime import date

import pytest
import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "alfianfahrur@gmail.com"
ADMIN_PASSWORD = "SwarnaAdmin#2026"


@pytest.fixture(scope="module")
def state():
    """Create isolated companies and hold IDs/tokens for this run's API checks."""
    if not BASE_URL:
        pytest.fail("REACT_APP_BACKEND_URL must be exported when running this test")
    s = {"admin": requests.Session()}
    s["admin"].headers.update({"Content-Type": "application/json"})
    login = s["admin"].post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert login.status_code == 200, login.text
    s["admin_token"] = login.json()["token"]
    s["admin"].headers.update({"Authorization": f"Bearer {s['admin_token']}"})

    suffix = uuid.uuid4().hex[:10]
    s["company_a_resp"] = s["admin"].post(
        f"{BASE_URL}/api/companies",
        json={"name": f"TEST_r3_A_{suffix}", "admin_email": f"test.r3.a.{suffix}@example.com", "admin_name": "R3 Company A Admin"},
        timeout=30,
    )
    assert s["company_a_resp"].status_code == 200, s["company_a_resp"].text
    s["company_a"] = s["company_a_resp"].json()["company"]
    s["a_token_invite"] = s["company_a_resp"].json()["invite_token"]
    s["company_a_id"] = s["company_a"]["id"]

    s["company_b_resp"] = s["admin"].post(
        f"{BASE_URL}/api/companies",
        json={"name": f"TEST_r3_B_{suffix}", "admin_email": f"test.r3.b.{suffix}@example.com", "admin_name": "R3 Company B Admin"},
        timeout=30,
    )
    assert s["company_b_resp"].status_code == 200, s["company_b_resp"].text
    s["company_b"] = s["company_b_resp"].json()["company"]
    s["b_token_invite"] = s["company_b_resp"].json()["invite_token"]
    s["company_b_id"] = s["company_b"]["id"]

    s["a_accept"] = requests.post(
        f"{BASE_URL}/api/invitations/accept",
        json={"token": s["a_token_invite"], "name": "R3 Company A Admin", "password": "R3-A-Password#2026", "phone": ""},
        timeout=30,
    )
    assert s["a_accept"].status_code == 200, s["a_accept"].text
    s["a_token"] = s["a_accept"].json()["token"]
    s["a"] = requests.Session()
    s["a"].headers.update({"Content-Type": "application/json", "Authorization": f"Bearer {s['a_token']}"})

    s["b_accept"] = requests.post(
        f"{BASE_URL}/api/invitations/accept",
        json={"token": s["b_token_invite"], "name": "R3 Company B Admin", "password": "R3-B-Password#2026", "phone": ""},
        timeout=30,
    )
    assert s["b_accept"].status_code == 200, s["b_accept"].text
    s["b_token"] = s["b_accept"].json()["token"]
    s["b"] = requests.Session()
    s["b"].headers.update({"Content-Type": "application/json", "Authorization": f"Bearer {s['b_token']}"})
    s["qa"] = {"company_id": s["company_a_id"]}
    s["qb"] = {"company_id": s["company_b_id"]}
    return s


def test_01_login_me_and_access_token(state):
    me = state["admin"].get(f"{BASE_URL}/api/auth/me", timeout=30)
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == ADMIN_EMAIL
    assert body["role"] == "swarna_admin"
    assert "password_hash" not in body


def test_02_company_creation_and_invite_validation(state):
    for key in ("company_a_resp", "company_b_resp"):
        data = state[key].json()
        assert data["company"]["id"]
        assert data["invite_token"]
        assert data["company"]["status_pendaftaran"] == "diundang"
    valid = requests.get(f"{BASE_URL}/api/invitations/validate/{state['a_token_invite']}", timeout=30)
    assert valid.status_code == 404  # the setup accepted it; used tokens are no longer valid
    companies = state["admin"].get(f"{BASE_URL}/api/companies", timeout=30)
    assert companies.status_code == 200
    ids = {c["id"] for c in companies.json()}
    assert {state["company_a_id"], state["company_b_id"]}.issubset(ids)


def test_03_invite_single_use_and_team_member(state):
    reaccept = requests.post(
        f"{BASE_URL}/api/invitations/accept",
        json={"token": state["a_token_invite"], "name": "Replay", "password": "Replay#2026"},
        timeout=30,
    )
    assert reaccept.status_code in (404, 409, 410)
    invite = state["a"].post(
        f"{BASE_URL}/api/invitations?company_id={state['company_a_id']}",
        json={"email": f"test.r3.hrga.{uuid.uuid4().hex[:8]}@example.com", "role": "hrga", "name": "R3 HRGA"},
        timeout=30,
    )
    assert invite.status_code == 200, invite.text
    inv = invite.json()["invite"]
    assert inv["role"] == "hrga"
    assert inv["company_id"] == state["company_a_id"]
    valid = requests.get(f"{BASE_URL}/api/invitations/validate/{inv['token']}", timeout=30)
    assert valid.status_code == 200
    assert valid.json()["role"] == "hrga"


def test_04_site_crud(state):
    q = state["qa"]
    created = state["a"].post(f"{BASE_URL}/api/sites", params=q, json={"name": "R3 Site A", "address": "Jalan Test 1"}, timeout=30)
    assert created.status_code == 200, created.text
    site = created.json()
    assert site["name"] == "R3 Site A"
    state["site_id"] = site["id"]
    listed = state["a"].get(f"{BASE_URL}/api/sites", params=q, timeout=30)
    assert listed.status_code == 200
    assert any(row["id"] == site["id"] for row in listed.json())
    updated = state["a"].put(f"{BASE_URL}/api/sites/{site['id']}", params=q, json={"name": "R3 Site A Updated", "address": "Updated"}, timeout=30)
    assert updated.status_code == 200
    assert updated.json()["name"] == "R3 Site A Updated"


def test_05_monitoring_point_crud_and_due_date(state):
    q = state["qa"]
    payload = {
        "site_id": state["site_id"], "name": "R3 pH Point", "jenis": "air_limbah", "frekuensi_bulan": 1,
        "tanggal_uji_terakhir": "2026-01-31",
        "parameters": [{"nama": "pH", "satuan": "-", "baku_mutu": 8, "baku_mutu_min": 6}, {"nama": "COD", "satuan": "mg/L", "baku_mutu": 100}],
    }
    created = state["a"].post(f"{BASE_URL}/api/monitoring-points", params=q, json=payload, timeout=30)
    assert created.status_code == 200, created.text
    point = created.json()
    assert point["tanggal_jatuh_tempo_berikutnya"] == "2026-02-28"
    assert len(point["parameters"]) == 2
    state["point_id"] = point["id"]
    fetched = state["a"].get(f"{BASE_URL}/api/monitoring-points/{point['id']}", params=q, timeout=30)
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "R3 pH Point"
    payload["name"] = "R3 pH Point Updated"
    payload["frekuensi_bulan"] = 6
    updated = state["a"].put(f"{BASE_URL}/api/monitoring-points/{point['id']}", params=q, json=payload, timeout=30)
    assert updated.status_code == 200
    assert updated.json()["name"] == "R3 pH Point Updated"
    assert updated.json()["tanggal_jatuh_tempo_berikutnya"] == "2026-07-31"


def test_06_lab_crud(state):
    q = state["qa"]
    created = state["a"].post(f"{BASE_URL}/api/labs", params=q, json={"nama": "R3 Accredited Lab", "akreditasi_kan": True, "narahubung": "R3 Contact", "no_hp": "0812", "catatan": "test"}, timeout=30)
    assert created.status_code == 200, created.text
    lab = created.json()
    assert lab["nama"] == "R3 Accredited Lab"
    state["lab_id"] = lab["id"]
    updated = state["a"].put(f"{BASE_URL}/api/labs/{lab['id']}", params=q, json={"nama": "R3 Lab Updated", "akreditasi_kan": True, "narahubung": "Updated", "no_hp": "0813", "catatan": "updated"}, timeout=30)
    assert updated.status_code == 200
    assert updated.json()["nama"] == "R3 Lab Updated"
    listed = state["a"].get(f"{BASE_URL}/api/labs", params=q, timeout=30)
    assert listed.status_code == 200
    assert any(row["id"] == lab["id"] for row in listed.json())


def test_07_lhu_upload_evaluation_and_download(state):
    q = state["qa"]
    form = {"periode": "2026-08", "tanggal_uji": "2026-08-01", "lab_id": state["lab_id"], "results": json.dumps([{"nama": "pH", "nilai": 9}, {"nama": "COD", "nilai": 50}])}
    state["a"].headers.pop("Content-Type", None)
    uploaded = state["a"].post(f"{BASE_URL}/api/monitoring-points/{state['point_id']}/lhu", params=q, data=form, files={"file": ("r3-report.pdf", b"R3 PDF bytes", "application/pdf")}, timeout=120)
    assert uploaded.status_code == 200, uploaded.text
    report = uploaded.json()
    assert report["results"][0]["status"] == "melebihi"
    assert report["results"][1]["status"] == "sesuai"
    assert report["content_type"] == "application/pdf"
    assert report["storage_path"]
    assert report["size"] == len(b"R3 PDF bytes")
    state["report_id"] = report["id"]
    point = state["a"].get(f"{BASE_URL}/api/monitoring-points/{state['point_id']}", params=q, timeout=30)
    assert point.status_code == 200
    assert point.json()["tanggal_uji_terakhir"] == "2026-08-01"
    assert point.json()["tanggal_jatuh_tempo_berikutnya"] == "2027-02-01"
    listed = state["a"].get(f"{BASE_URL}/api/monitoring-points/{state['point_id']}/lhu", params=q, timeout=30)
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == state["report_id"]
    downloaded = state["a"].get(f"{BASE_URL}/api/files/{report['storage_path']}", timeout=120)
    assert downloaded.status_code == 200
    assert downloaded.content == b"R3 PDF bytes"


def test_08_lhu_trend_and_compliance(state):
    q = state["qa"]
    form = {"periode": "2026-09", "tanggal_uji": "2026-09-01", "lab_id": state["lab_id"], "results": json.dumps([{"nama": "pH", "nilai": 7, "baku_mutu": 8, "baku_mutu_min": 6}, {"nama": "COD", "nilai": 40, "baku_mutu": 100}])}
    state["a"].headers.pop("Content-Type", None)
    uploaded = state["a"].post(f"{BASE_URL}/api/monitoring-points/{state['point_id']}/lhu", params=q, data=form, files={"file": ("r3-report-2.pdf", b"R3 PDF bytes 2", "application/pdf")}, timeout=120)
    assert uploaded.status_code == 200, uploaded.text
    state["report_id_2"] = uploaded.json()["id"]
    trend = state["a"].get(f"{BASE_URL}/api/monitoring-points/{state['point_id']}/trend", params={**q, "parameter": "pH"}, timeout=30)
    assert trend.status_code == 200
    trend_body = trend.json()
    assert len(trend_body["series"]) == 2
    assert trend_body["series"][0]["nilai"] == 9
    assert trend_body["series"][1]["nilai"] == 7
    assert trend_body["change_percent"] == -22.2
    assert trend_body["baku_mutu"] == 8
    compliance = state["a"].get(f"{BASE_URL}/api/compliance", params=q, timeout=30)
    assert compliance.status_code == 200
    assert set(("percent", "color", "taat", "total", "detail")).issubset(compliance.json())


def test_09_dashboard_and_lhu_soft_delete(state):
    q = state["qa"]
    # Create an overdue/no-report point for dashboard categorization.
    point = state["a"].post(f"{BASE_URL}/api/monitoring-points", params=q, json={"site_id": state["site_id"], "name": "R3 Overdue Point", "jenis": "emisi", "frekuensi_bulan": 1, "tanggal_uji_terakhir": "2020-01-01", "parameters": []}, timeout=30)
    assert point.status_code == 200
    state["overdue_point_id"] = point.json()["id"]
    dashboard = state["a"].get(f"{BASE_URL}/api/dashboard", params=q, timeout=30)
    assert dashboard.status_code == 200
    body = dashboard.json()
    assert {"overdue", "due_7", "due_14", "due_30", "total_points", "compliance"}.issubset(body)
    assert any(row["id"] == state["overdue_point_id"] for row in body["overdue"])
    deleted = state["a"].delete(f"{BASE_URL}/api/lhu/{state['report_id']}", params=q, timeout=30)
    assert deleted.status_code == 200
    listed = state["a"].get(f"{BASE_URL}/api/monitoring-points/{state['point_id']}/lhu", params=q, timeout=30)
    assert listed.status_code == 200
    assert all(row["id"] != state["report_id"] for row in listed.json())


def test_10_whatsapp_settings_masking(state):
    get_before = state["admin"].get(f"{BASE_URL}/api/settings/whatsapp", timeout=30)
    assert get_before.status_code == 200
    update = state["admin"].put(f"{BASE_URL}/api/settings/whatsapp", json={"enabled": False, "api_url": "https://example.com/wa", "api_key": "r3-secret", "sender_number": "0812"}, timeout=30)
    assert update.status_code == 200
    body = update.json()
    assert body["api_key"] == "****"
    assert body["configured"] is False
    # Do not enable the fake WhatsApp endpoint for other concurrent tests.
    state["admin"].put(f"{BASE_URL}/api/settings/whatsapp", json={"enabled": False, "api_url": "", "api_key": "****", "sender_number": ""}, timeout=30)


def test_11_reminders_notifications_and_cron_auth(state):
    run_now = state["admin"].post(f"{BASE_URL}/api/reminders/run-now", timeout=120)
    assert run_now.status_code == 200, run_now.text
    assert run_now.json()["ok"] is True
    logs = state["a"].get(f"{BASE_URL}/api/notifications", params=state["qa"], timeout=30)
    assert logs.status_code == 200
    assert isinstance(logs.json(), list)
    no_auth = requests.post(f"{BASE_URL}/api/cron/reminders", timeout=30)
    assert no_auth.status_code == 401
    wrong = requests.post(f"{BASE_URL}/api/cron/reminders", headers={"Authorization": "Bearer definitely-wrong"}, timeout=30)
    assert wrong.status_code == 401
    secret = os.environ.get("WEBHOOK_CRON_SECRET", "")
    assert secret, "WEBHOOK_CRON_SECRET must be exported for cron verification"
    accepted = requests.post(f"{BASE_URL}/api/cron/reminders", headers={"Authorization": f"Bearer {secret}"}, timeout=30)
    assert accepted.status_code == 200
    assert accepted.json()["accepted"] is True


def test_12_row_level_security_across_companies(state):
    a = state["company_a_id"]
    b = state["company_b_id"]
    checks = [
        state["b"].get(f"{BASE_URL}/api/sites", params={"company_id": a}, timeout=30),
        state["b"].get(f"{BASE_URL}/api/monitoring-points", params={"company_id": a}, timeout=30),
        state["b"].get(f"{BASE_URL}/api/labs", params={"company_id": a}, timeout=30),
        state["b"].get(f"{BASE_URL}/api/dashboard", params={"company_id": a}, timeout=30),
        state["b"].get(f"{BASE_URL}/api/notifications", params={"company_id": a}, timeout=30),
        state["b"].get(f"{BASE_URL}/api/monitoring-points/{state['point_id']}/lhu", params={"company_id": a}, timeout=30),
        state["b"].post(f"{BASE_URL}/api/sites", params={"company_id": a}, json={"name": "cross-company", "address": "bad"}, timeout=30),
    ]
    assert [r.status_code for r in checks] == [403] * len(checks), [(r.status_code, r.text) for r in checks]
    own = state["b"].get(f"{BASE_URL}/api/sites", params={"company_id": b}, timeout=30)
    assert own.status_code == 200
    bsite = state["b"].post(f"{BASE_URL}/api/sites", params={"company_id": b}, json={"name": "R3 B Site", "address": "B"}, timeout=30)
    assert bsite.status_code == 200
    cross_update = state["a"].put(f"{BASE_URL}/api/monitoring-points/{state['point_id']}", params={"company_id": a}, json={"site_id": bsite.json()["id"], "name": "cross-company", "jenis": "air_limbah", "frekuensi_bulan": 6, "tanggal_uji_terakhir": "2026-08-01", "parameters": []}, timeout=30)
    assert cross_update.status_code in (400, 403), (cross_update.status_code, cross_update.text)


def test_13_delete_site_and_point(state):
    q = state["qa"]
    deleted_point = state["a"].delete(f"{BASE_URL}/api/monitoring-points/{state['overdue_point_id']}", params=q, timeout=30)
    assert deleted_point.status_code == 200
    deleted_site = state["a"].delete(f"{BASE_URL}/api/sites/{state['site_id']}", params=q, timeout=30)
    assert deleted_site.status_code == 200
    deleted_lab = state["a"].delete(f"{BASE_URL}/api/labs/{state['lab_id']}", params=q, timeout=30)
    assert deleted_lab.status_code == 200
    assert state["a"].get(f"{BASE_URL}/api/sites", params=q, timeout=30).status_code == 200


def test_14_cors_explicit_origin_and_auth_failure(state):
    origin = "https://gh-sync-20.preview.emergentagent.com"
    options = requests.options(f"{BASE_URL}/api/auth/login", headers={"Origin": origin, "Access-Control-Request-Method": "POST"}, timeout=30)
    assert options.status_code == 200
    assert options.headers.get("access-control-allow-credentials") == "true"
    assert options.headers.get("access-control-allow-origin") == origin
    wrong = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": "wrong-r3-password"}, timeout=30)
    assert wrong.status_code == 401


def test_15_brute_force_lockout_after_five_failures(state):
    for _ in range(5):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": "wrong-r3-password"}, timeout=30)
        assert response.status_code == 401
    locked = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert locked.status_code in (401, 429), f"No lockout after five failed attempts: {locked.status_code} {locked.text}"


def test_16_seeded_company_admin_and_misc_read_routes(state):
    seeded = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "budi.hrga@hijaulestari.co.id", "password": "Budi#2026"}, timeout=30)
    assert seeded.status_code == 200, seeded.text
    seeded_token = seeded.json()["token"]
    seeded_session = requests.Session()
    seeded_session.headers.update({"Authorization": f"Bearer {seeded_token}"})
    me = seeded_session.get(f"{BASE_URL}/api/auth/me", timeout=30)
    assert me.status_code == 200
    assert me.json()["email"] == "budi.hrga@hijaulestari.co.id"
    assert me.json()["role"] in ("company_admin", "hrga")
    companies = seeded_session.get(f"{BASE_URL}/api/companies", timeout=30)
    assert companies.status_code == 200
    assert len(companies.json()) >= 1
    cid = companies.json()[0]["id"]
    users = seeded_session.get(f"{BASE_URL}/api/users", params={"company_id": cid}, timeout=30)
    invites = seeded_session.get(f"{BASE_URL}/api/invitations", params={"company_id": cid}, timeout=30)
    assert users.status_code == 200
    assert invites.status_code == 200
    assert all("password_hash" not in user for user in users.json())
    company = seeded_session.get(f"{BASE_URL}/api/companies/{cid}", timeout=30)
    assert company.status_code == 200
    logout = seeded_session.post(f"{BASE_URL}/api/auth/logout", timeout=30)
    assert logout.status_code == 200


def test_17_invalid_auth_and_missing_resources(state):
    unauth = requests.get(f"{BASE_URL}/api/sites", timeout=30)
    assert unauth.status_code == 401
    missing = state["admin"].get(f"{BASE_URL}/api/companies/not-a-real-company", timeout=30)
    assert missing.status_code == 403

