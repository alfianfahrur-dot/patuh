"""Run r2 backend integration coverage for auth, RLS, CRUD, LHU, and reminders."""
import json
import os
import uuid
from datetime import date, timedelta

import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
ADMIN_EMAIL = "alfianfahrur@gmail.com"
ADMIN_PASSWORD = "SwarnaAdmin#2026"


def response_json(response):
    try:
        return response.json()
    except ValueError:
        pytest.fail(f"Expected JSON from {response.request.method} {response.url}, got {response.status_code}: {response.text[:500]}")


def expect(response, status, label):
    if response.status_code != status:
        pytest.fail(f"{label}: expected {status}, got {response.status_code}: {response.text[:500]}")
    return response_json(response)


@pytest.fixture(scope="session")
def state():
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    suffix = uuid.uuid4().hex[:10]
    admin_login = session.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30,
    )
    admin_payload = expect(admin_login, 200, "seeded admin login")
    assert admin_payload["user"]["role"] == "swarna_admin"
    admin_token = admin_payload["token"]
    headers = {"Authorization": f"Bearer {admin_token}"}
    companies = []
    admins = []
    for label in ("A", "B"):
        email = f"r2-{suffix}-{label.lower()}@r2.example.com"
        created = session.post(
            f"{BASE_URL}/api/companies",
            headers=headers,
            json={"name": f"R2 Isolated Company {label} {suffix}", "admin_email": email, "admin_name": f"R2 Admin {label}"},
            timeout=30,
        )
        body = expect(created, 200, f"create company {label}")
        assert body["invite_token"]
        company = body["company"]
        validate = session.get(f"{BASE_URL}/api/invitations/validate/{body['invite_token']}", timeout=30)
        validate_body = expect(validate, 200, f"validate company {label} invite")
        assert validate_body["email"] == email
        accepted = session.post(
            f"{BASE_URL}/api/invitations/accept",
            json={"token": body["invite_token"], "name": f"R2 Admin {label}", "password": f"R2Pass-{suffix}-{label}"},
            timeout=30,
        )
        accepted_body = expect(accepted, 200, f"accept company {label} invite")
        assert accepted_body["user"]["role"] == "company_admin"
        assert accepted_body["user"]["company_id"] == company["id"]
        companies.append(company)
        admins.append({"email": email, "token": accepted_body["token"], "user": accepted_body["user"]})
        reused = session.post(
            f"{BASE_URL}/api/invitations/accept",
            json={"token": body["invite_token"], "name": "Reuse", "password": "ReusePass-123"},
            timeout=30,
        )
        assert reused.status_code in (404, 409, 410), f"single-use invite unexpectedly accepted: {reused.status_code} {reused.text}"
    return {"session": session, "suffix": suffix, "admin_token": admin_token, "admin_headers": headers, "companies": companies, "admins": admins}


def h(token):
    return {"Authorization": f"Bearer {token}"}


# Auth and invitation behavior.
def test_auth_me_and_existing_seeded_user(state):
    session = state["session"]
    me = session.get(f"{BASE_URL}/api/auth/me", headers=state["admin_headers"], timeout=30)
    me_body = expect(me, 200, "admin auth/me")
    assert me_body["email"] == ADMIN_EMAIL
    assert "password_hash" not in me_body
    missing = session.get(f"{BASE_URL}/api/auth/me", timeout=30)
    assert missing.status_code == 401
    seeded = session.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "budi.hrga@hijaulestari.co.id", "password": "Budi#2026"},
        timeout=30,
    )
    # The seeded company-admin credential is part of the requested test contract.
    seeded_body = expect(seeded, 200, "seeded company admin login")
    assert seeded_body["user"]["role"] == "company_admin"


# Invite-only team member flow.
def test_team_invite_validate_and_accept(state):
    session = state["session"]
    company = state["companies"][0]
    company_admin = state["admins"][0]
    suffix = state["suffix"]
    email = f"r2-{suffix}-hrga@r2.example.com"
    invited = session.post(
        f"{BASE_URL}/api/invitations?company_id={company['id']}",
        headers=h(company_admin["token"]),
        json={"email": email, "role": "hrga", "name": "R2 HRGA"},
        timeout=30,
    )
    invited_body = expect(invited, 200, "invite HRGA")
    token = invited_body["invite"]["token"]
    assert invited_body["invite"]["company_id"] == company["id"]
    validated = session.get(f"{BASE_URL}/api/invitations/validate/{token}", timeout=30)
    validated_body = expect(validated, 200, "validate HRGA invite")
    assert validated_body["role"] == "hrga"
    accepted = session.post(
        f"{BASE_URL}/api/invitations/accept",
        json={"token": token, "name": "R2 HRGA", "password": f"R2Hrga-{suffix}"},
        timeout=30,
    )
    accepted_body = expect(accepted, 200, "accept HRGA invite")
    assert accepted_body["user"]["role"] == "hrga"
    assert accepted_body["user"]["company_id"] == company["id"]
    invalid_role = session.post(
        f"{BASE_URL}/api/invitations?company_id={company['id']}",
        headers=h(company_admin["token"]),
        json={"email": f"r2-{suffix}-invalid@r2.example.com", "role": "swarna_admin", "name": "Invalid"},
        timeout=30,
    )
    assert invalid_role.status_code == 400


# Sites and monitoring points, including automatic next due date.
def test_sites_and_monitoring_point_crud_due_date(state):
    session = state["session"]
    company = state["companies"][0]
    token = state["admins"][0]["token"]
    q = f"?company_id={company['id']}"
    site = expect(session.post(f"{BASE_URL}/api/sites{q}", headers=h(token), json={"name": "R2 Site", "address": "R2 Address"}, timeout=30), 200, "create site")
    assert site["company_id"] == company["id"]
    sites = expect(session.get(f"{BASE_URL}/api/sites{q}", headers=h(token), timeout=30), 200, "list sites")
    assert any(x["id"] == site["id"] for x in sites)
    last_test = "2025-01-31"
    point = expect(session.post(
        f"{BASE_URL}/api/monitoring-points{q}", headers=h(token),
        json={"site_id": site["id"], "name": "R2 Stack Point", "jenis": "emisi", "frekuensi_bulan": 6,
              "tanggal_uji_terakhir": last_test,
              "parameters": [{"nama": "pH", "satuan": "-", "baku_mutu": 7.0}, {"nama": "TSS", "satuan": "mg/L", "baku_mutu": 100}]},
        timeout=30), 200, "create monitoring point")
    assert point["tanggal_jatuh_tempo_berikutnya"] == "2025-07-31"
    assert len(point["parameters"]) == 2
    fetched = expect(session.get(f"{BASE_URL}/api/monitoring-points/{point['id']}{q}", headers=h(token), timeout=30), 200, "get monitoring point")
    assert fetched["site_name"] == "R2 Site"
    updated = expect(session.put(f"{BASE_URL}/api/monitoring-points/{point['id']}{q}", headers=h(token), json={
        "site_id": site["id"], "name": "R2 Stack Point Updated", "jenis": "emisi", "frekuensi_bulan": 12,
        "tanggal_uji_terakhir": "2025-02-28", "parameters": [{"nama": "pH", "satuan": "-", "baku_mutu": 8.0}],
    }, timeout=30), 200, "update monitoring point")
    assert updated["name"] == "R2 Stack Point Updated"
    assert updated["tanggal_jatuh_tempo_berikutnya"] == "2026-02-28"
    state["site"] = site
    state["point"] = updated


# Laboratory directory CRUD.
def test_lab_crud(state):
    session = state["session"]
    company = state["companies"][0]
    token = state["admins"][0]["token"]
    q = f"?company_id={company['id']}"
    lab = expect(session.post(f"{BASE_URL}/api/labs{q}", headers=h(token), json={"nama": "R2 Lab", "akreditasi_kan": True, "narahubung": "R2 Contact", "no_hp": "0812", "catatan": "R2"}, timeout=30), 200, "create lab")
    assert lab["company_id"] == company["id"]
    labs = expect(session.get(f"{BASE_URL}/api/labs{q}", headers=h(token), timeout=30), 200, "list labs")
    assert any(x["id"] == lab["id"] for x in labs)
    edited = expect(session.put(f"{BASE_URL}/api/labs/{lab['id']}{q}", headers=h(token), json={"nama": "R2 Lab Edited", "akreditasi_kan": False, "narahubung": "", "no_hp": "", "catatan": "edited"}, timeout=30), 200, "update lab")
    assert edited["nama"] == "R2 Lab Edited"
    state["lab"] = edited


# LHU upload evaluates parameters, persists files, updates due date, and supports trend.
def test_lhu_upload_file_list_download_trend_and_soft_delete(state):
    session = state["session"]
    company = state["companies"][0]
    token = state["admins"][0]["token"]
    q = f"?company_id={company['id']}"
    point = state["point"]
    lab = state["lab"]
    common = {"lab_id": lab["id"], "results": json.dumps([{"nama": "pH", "nilai": 7.2, "satuan": "-", "baku_mutu": 7.0}])}
    upload_session = requests.Session()
    first = upload_session.post(
        f"{BASE_URL}/api/monitoring-points/{point['id']}/lhu{q}", headers=h(token), files={"file": ("r2-first.pdf", b"R2 PDF first", "application/pdf")}, data={"periode": "2025-01", "tanggal_uji": "2025-01-15", **common}, timeout=120)
    first_body = expect(first, 200, "upload first LHU")
    assert first_body["results"][0]["status"] == "melebihi"
    assert first_body["storage_path"]
    second = upload_session.post(f"{BASE_URL}/api/monitoring-points/{point['id']}/lhu{q}", headers=h(token), files={"file": ("r2-second.pdf", b"R2 PDF second", "application/pdf")}, data={"periode": "2025-07", "tanggal_uji": "2025-07-15", "lab_id": lab["id"], "results": json.dumps([{ "nama": "pH", "nilai": 6.5, "satuan": "-", "baku_mutu": 7.0 }])}, timeout=120)
    second_body = expect(second, 200, "upload second LHU")
    assert second_body["results"][0]["status"] == "sesuai"
    fetched_point = expect(session.get(f"{BASE_URL}/api/monitoring-points/{point['id']}{q}", headers=h(token), timeout=30), 200, "point after LHU")
    assert fetched_point["tanggal_uji_terakhir"] == "2025-07-15"
    assert fetched_point["tanggal_jatuh_tempo_berikutnya"] == "2026-07-15"
    reports = expect(session.get(f"{BASE_URL}/api/monitoring-points/{point['id']}/lhu{q}", headers=h(token), timeout=30), 200, "list LHU")
    assert [x["tanggal_uji"] for x in reports[:2]] == ["2025-07-15", "2025-01-15"]
    assert reports[0]["lab_name"] == "R2 Lab Edited"
    downloaded = session.get(f"{BASE_URL}/api/files/{first_body['storage_path']}", headers=h(token), timeout=120)
    assert downloaded.status_code == 200
    assert downloaded.content == b"R2 PDF first"
    trend = expect(session.get(f"{BASE_URL}/api/monitoring-points/{point['id']}/trend{q}&parameter=pH", headers=h(token), timeout=30), 200, "pH trend")
    assert [x["nilai"] for x in trend["series"]] == [7.2, 6.5]
    assert trend["change_percent"] == -9.7
    assert trend["baku_mutu"] == 8.0
    deleted = expect(session.delete(f"{BASE_URL}/api/lhu/{first_body['id']}{q}", headers=h(token), timeout=30), 200, "soft-delete LHU")
    assert deleted["ok"] is True
    remaining = expect(session.get(f"{BASE_URL}/api/monitoring-points/{point['id']}/lhu{q}", headers=h(token), timeout=30), 200, "list LHU after delete")
    assert all(x["id"] != first_body["id"] for x in remaining)
    state["first_lhu"] = first_body


# Dashboard, compliance, notifications, platform settings, and cron authorization.
def test_dashboard_compliance_reminders_settings_and_cron(state):
    session = state["session"]
    company = state["companies"][0]
    admin_headers = state["admin_headers"]
    company_token = state["admins"][0]["token"]
    q = f"?company_id={company['id']}"
    dashboard = expect(session.get(f"{BASE_URL}/api/dashboard{q}", headers=h(company_token), timeout=30), 200, "dashboard")
    for key in ("overdue", "due_7", "due_14", "due_30", "total_points", "ok_count", "compliance"):
        assert key in dashboard
    compliance = expect(session.get(f"{BASE_URL}/api/compliance{q}", headers=h(company_token), timeout=30), 200, "compliance")
    assert isinstance(compliance["percent"], int)
    assert compliance["color"] in ("green", "yellow", "red")
    notifications_before = expect(session.get(f"{BASE_URL}/api/notifications{q}", headers=h(company_token), timeout=30), 200, "notifications before reminders")
    assert isinstance(notifications_before, list)
    settings = expect(session.get(f"{BASE_URL}/api/settings/whatsapp", headers=admin_headers, timeout=30), 200, "get WhatsApp settings")
    assert settings["api_key"] in ("", "****")
    configured = expect(session.put(f"{BASE_URL}/api/settings/whatsapp", headers=admin_headers, json={"enabled": True, "api_url": "https://wa.example.test/send", "api_key": "r2-secret", "sender_number": "0812"}, timeout=30), 200, "set WhatsApp settings")
    assert configured["api_key"] == "****"
    assert configured["configured"] is True
    masked = expect(session.put(f"{BASE_URL}/api/settings/whatsapp", headers=admin_headers, json={"enabled": False, "api_url": "", "api_key": "****", "sender_number": ""}, timeout=30), 200, "mask WhatsApp settings")
    assert masked["api_key"] == "****"
    now = session.post(f"{BASE_URL}/api/reminders/run-now", headers=admin_headers, timeout=120)
    now_body = expect(now, 200, "run reminders now")
    assert now_body["ok"] is True
    cron_without = session.post(f"{BASE_URL}/api/cron/reminders", timeout=30)
    assert cron_without.status_code == 401
    cron_bad = session.post(f"{BASE_URL}/api/cron/reminders", headers={"Authorization": "Bearer wrong-secret"}, timeout=30)
    assert cron_bad.status_code == 401
    secret = os.environ["WEBHOOK_CRON_SECRET"]
    cron_good = session.post(f"{BASE_URL}/api/cron/reminders", headers={"Authorization": f"Bearer {secret}"}, timeout=30)
    assert cron_good.status_code == 200
    assert response_json(cron_good)["accepted"] is True
    notifications_after = expect(session.get(f"{BASE_URL}/api/notifications{q}", headers=h(company_token), timeout=30), 200, "notifications after reminders")
    assert isinstance(notifications_after, list)


# Row-level security across all scoped resource families.
def test_company_rls_blocks_cross_company_reads_and_writes(state):
    session = state["session"]
    company_a, company_b = state["companies"]
    token_a = state["admins"][0]["token"]
    token_b = state["admins"][1]["token"]
    q_b = f"?company_id={company_b['id']}"
    for path in ("sites", "monitoring-points", "labs", "dashboard", "compliance", "notifications"):
        blocked = session.get(f"{BASE_URL}/api/{path}{q_b}", headers=h(token_a), timeout=30)
        assert blocked.status_code == 403, f"cross-company GET {path} returned {blocked.status_code}: {blocked.text}"
    blocked_post = session.post(f"{BASE_URL}/api/sites{q_b}", headers=h(token_a), json={"name": "Should Not Exist", "address": ""}, timeout=30)
    assert blocked_post.status_code == 403
    if "site" in state:
        blocked_put = session.put(f"{BASE_URL}/api/sites/{state['site']['id']}{q_b}", headers=h(token_a), json={"name": "Should Not Update", "address": ""}, timeout=30)
        assert blocked_put.status_code == 403
    companies = expect(session.get(f"{BASE_URL}/api/companies", headers=state["admin_headers"], timeout=30), 200, "admin company assignments")
    ids = {x["id"] for x in companies}
    assert company_a["id"] in ids and company_b["id"] in ids
    own = expect(session.get(f"{BASE_URL}/api/sites?company_id={company_a['id']}", headers=h(token_a), timeout=30), 200, "company A own sites")
    foreign = expect(session.get(f"{BASE_URL}/api/sites?company_id={company_b['id']}", headers=h(token_b), timeout=30), 200, "company B own sites")
    assert all(x["company_id"] == company_a["id"] for x in own)
    assert all(x["company_id"] == company_b["id"] for x in foreign)
    foreign_site = expect(session.post(f"{BASE_URL}/api/sites{q_b}", headers=h(token_b), json={"name": "R2 B Site", "address": ""}, timeout=30), 200, "create company B site")
    b_point = expect(session.post(f"{BASE_URL}/api/monitoring-points{q_b}", headers=h(token_b), json={
        "site_id": foreign_site["id"], "name": "R2 B Point", "jenis": "air_limbah", "frekuensi_bulan": 6,
        "tanggal_uji_terakhir": None, "parameters": [{"nama": "pH", "satuan": "-", "baku_mutu": 7.0}],
    }, timeout=30), 200, "create company B point")
    upload_b_session = requests.Session()
    b_lhu = upload_b_session.post(f"{BASE_URL}/api/monitoring-points/{b_point['id']}/lhu{q_b}", headers=h(token_b), files={"file": ("r2-b.pdf", b"R2 B PDF", "application/pdf")}, data={
        "periode": "2025-08", "tanggal_uji": "2025-08-01", "lab_id": "", "results": json.dumps([{ "nama": "pH", "nilai": 6.5, "baku_mutu": 7.0 }])}, timeout=120)
    b_lhu_body = expect(b_lhu, 200, "upload company B LHU")
    blocked_b_lhu = session.get(f"{BASE_URL}/api/monitoring-points/{b_point['id']}/lhu{q_b}", headers=h(token_a), timeout=30)
    assert blocked_b_lhu.status_code == 403
    blocked_b_file = session.get(f"{BASE_URL}/api/files/{b_lhu_body['storage_path']}?company_id={company_b['id']}", headers=h(token_a), timeout=120)
    assert blocked_b_file.status_code == 403
    q_a = f"?company_id={company_a['id']}"
    point = state["point"]
    cross_site_update = session.put(f"{BASE_URL}/api/monitoring-points/{point['id']}{q_a}", headers=h(token_a), json={
        "site_id": foreign_site["id"], "name": point["name"], "jenis": point["jenis"],
        "frekuensi_bulan": point["frekuensi_bulan"], "tanggal_uji_terakhir": point["tanggal_uji_terakhir"],
        "parameters": [{"nama": p["nama"], "satuan": p["satuan"], "baku_mutu": p["baku_mutu"], "baku_mutu_min": p["baku_mutu_min"]} for p in point["parameters"]],
    }, timeout=30)
    session.delete(f"{BASE_URL}/api/lhu/{b_lhu_body['id']}{q_b}", headers=h(token_b), timeout=30)
    session.delete(f"{BASE_URL}/api/monitoring-points/{b_point['id']}{q_b}", headers=h(token_b), timeout=30)
    session.delete(f"{BASE_URL}/api/sites/{foreign_site['id']}{q_b}", headers=h(token_b), timeout=30)
    assert cross_site_update.status_code == 400, f"monitoring point accepted a foreign-company site_id: {cross_site_update.status_code} {cross_site_update.text}"


# Delete paths and response data integrity.
def test_delete_point_site_and_lab(state):
    session = state["session"]
    company = state["companies"][0]
    token = state["admins"][0]["token"]
    q = f"?company_id={company['id']}"
    point = state["point"]
    site = state["site"]
    lab = state["lab"]
    assert expect(session.delete(f"{BASE_URL}/api/monitoring-points/{point['id']}{q}", headers=h(token), timeout=30), 200, "delete point")["ok"] is True
    missing_point = session.get(f"{BASE_URL}/api/monitoring-points/{point['id']}{q}", headers=h(token), timeout=30)
    assert missing_point.status_code == 404
    assert expect(session.delete(f"{BASE_URL}/api/sites/{site['id']}{q}", headers=h(token), timeout=30), 200, "delete site")["ok"] is True
    assert expect(session.delete(f"{BASE_URL}/api/labs/{lab['id']}{q}", headers=h(token), timeout=30), 200, "delete lab")["ok"] is True


# Optional auth hardening check from the auth playbook: login should lock out after repeated failures.
def test_bruteforce_lockout_after_five_failures(state):
    session = state["session"]
    statuses = []
    for _ in range(6):
        response = session.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": "definitely-wrong-r2"}, timeout=30)
        statuses.append(response.status_code)
    assert statuses[-1] in (423, 429), f"no brute-force lockout after 5 failures; statuses={statuses}"
