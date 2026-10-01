"""Backend regression tests for auth, invitations, scoped CRUD, LHU, analytics and RLS."""
import json
import os
import uuid
from datetime import date
from pathlib import Path

import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
RUN_ID = "r1_" + uuid.uuid4().hex[:10]
ADMIN_EMAIL = "alfianfahrur@gmail.com"
ADMIN_PASSWORD = "SwarnaAdmin#2026"
BUDI_EMAIL = "budi.hrga@hijaulestari.co.id"
BUDI_PASSWORD = "Budi#2026"


def api(session, method, path, **kwargs):
    response = session.request(method, f"{BASE_URL}{path}", timeout=45, **kwargs)
    print(f"{method} {path} -> {response.status_code}: {response.text[:400]}")
    return response


def bearer(token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}"})
    return s


@pytest.fixture(scope="module")
def state():
    """Create two isolated companies and admin sessions for this run."""
    admin = requests.Session()
    login = api(admin, "POST", "/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert login.status_code == 200, login.text
    token = login.json()["token"]
    swarna = bearer(token)

    def make_company(label):
        email = f"{RUN_ID}_{label}@r1testmail.com"
        r = api(swarna, "POST", "/api/companies", json={
            "name": f"{RUN_ID} {label}", "admin_email": email, "admin_name": f"{label} Admin"
        })
        assert r.status_code == 200, r.text
        payload = r.json()
        cid = payload["company"]["id"]
        invite_token = payload["invite_token"]
        valid = api(requests.Session(), "GET", f"/api/invitations/validate/{invite_token}")
        assert valid.status_code == 200, valid.text
        assert valid.json()["email"] == email.lower()
        accept = api(requests.Session(), "POST", "/api/invitations/accept", json={
            "token": invite_token, "name": f"{label} Admin", "password": f"Strong-{RUN_ID}-{label}!"
        })
        assert accept.status_code == 200, accept.text
        return {
            "id": cid,
            "admin_email": email,
            "invite_token": invite_token,
            "admin": bearer(accept.json()["token"]),
            "admin_user": accept.json()["user"],
        }

    a = make_company("A")
    b = make_company("B")
    return {"swarna": swarna, "admin_token": token, "a": a, "b": b}


def test_auth_login_and_me(state):
    swarna = state["swarna"]
    me = api(swarna, "GET", "/api/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == ADMIN_EMAIL
    assert me.json()["role"] == "swarna_admin"
    assert me.json().get("password_hash") is None
    assert state["admin_token"]


def test_seeded_company_admin_login_and_companies(state):
    session = requests.Session()
    login = api(session, "POST", "/api/auth/login", json={"email": BUDI_EMAIL, "password": BUDI_PASSWORD})
    assert login.status_code == 200, login.text
    user = login.json()["user"]
    assert user["role"] in ("company_admin", "hrga")
    assert user["company_id"]
    session = bearer(login.json()["token"])
    companies = api(session, "GET", "/api/companies")
    assert companies.status_code == 200
    assert any(c["id"] == user["company_id"] for c in companies.json())


def test_swarna_assignment_and_company_admin_invite(state):
    swarna = state["swarna"]
    a = state["a"]
    companies = api(swarna, "GET", "/api/companies")
    assert companies.status_code == 200
    assert a["id"] in [c["id"] for c in companies.json()]

    email = f"{RUN_ID}_hrga@r1testmail.com"
    invite = api(a["admin"], "POST", f"/api/invitations?company_id={a['id']}", json={
        "email": email, "role": "hrga", "name": "Run HRGA"
    })
    assert invite.status_code == 200, invite.text
    inv = invite.json()["invite"]
    assert inv["email"] == email and inv["role"] == "hrga"
    validated = api(requests.Session(), "GET", f"/api/invitations/validate/{inv['token']}")
    assert validated.status_code == 200
    accepted = api(requests.Session(), "POST", "/api/invitations/accept", json={
        "token": inv["token"], "name": "Run HRGA", "password": f"Strong-{RUN_ID}-hrga!"
    })
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["user"]["role"] == "hrga"
    again = api(requests.Session(), "POST", "/api/invitations/accept", json={
        "token": inv["token"], "name": "Run HRGA Again", "password": "Another-password!"
    })
    assert again.status_code in (404, 409, 410)


def test_sites_crud_and_company_scope(state):
    a = state["a"]
    s = a["admin"]
    created = api(s, "POST", f"/api/sites?company_id={a['id']}", json={"name": f"{RUN_ID} Site", "address": "Jl. Test 1"})
    assert created.status_code == 200, created.text
    site = created.json()
    assert site["name"] == f"{RUN_ID} Site" and site["company_id"] == a["id"]
    listed = api(s, "GET", f"/api/sites?company_id={a['id']}")
    assert listed.status_code == 200 and any(x["id"] == site["id"] for x in listed.json())
    updated = api(s, "PUT", f"/api/sites/{site['id']}?company_id={a['id']}", json={"name": f"{RUN_ID} Site Updated", "address": "Updated"})
    assert updated.status_code == 200 and updated.json()["name"] == f"{RUN_ID} Site Updated"
    state["site_a"] = site["id"]
    state["site_a_updated"] = updated.json()["id"]
    deleted = api(s, "DELETE", f"/api/sites/{site['id']}?company_id={a['id']}")
    assert deleted.status_code == 200 and deleted.json().get("ok") is True
    after = api(s, "GET", f"/api/sites?company_id={a['id']}")
    assert after.status_code == 200 and not any(x["id"] == site["id"] for x in after.json())


def test_monitoring_point_due_date_and_crud(state):
    a = state["a"]
    site = api(a["admin"], "POST", f"/api/sites?company_id={a['id']}", json={"name": f"{RUN_ID} Monitoring Site", "address": "Address"})
    assert site.status_code == 200
    site_id = site.json()["id"]
    payload = {
        "site_id": site_id, "name": f"{RUN_ID} Point", "jenis": "air_limbah", "frekuensi_bulan": 1,
        "tanggal_uji_terakhir": "2026-01-31",
        "parameters": [
            {"nama": "pH", "satuan": "-", "baku_mutu": 9.0, "baku_mutu_min": 6.0},
            {"nama": "COD", "satuan": "mg/L", "baku_mutu": 100.0},
        ],
    }
    created = api(a["admin"], "POST", f"/api/monitoring-points?company_id={a['id']}", json=payload)
    assert created.status_code == 200, created.text
    point = created.json()
    assert point["tanggal_jatuh_tempo_berikutnya"] == "2026-02-28"
    assert len(point["parameters"]) == 2 and all("id" in p for p in point["parameters"])
    got = api(a["admin"], "GET", f"/api/monitoring-points/{point['id']}?company_id={a['id']}")
    assert got.status_code == 200 and got.json()["id"] == point["id"]
    changed = dict(payload)
    changed["name"] = f"{RUN_ID} Point Updated"
    changed["tanggal_uji_terakhir"] = "2026-02-01"
    updated = api(a["admin"], "PUT", f"/api/monitoring-points/{point['id']}?company_id={a['id']}", json=changed)
    assert updated.status_code == 200 and updated.json()["name"] == changed["name"]
    assert updated.json()["tanggal_jatuh_tempo_berikutnya"] == "2026-03-01"
    state["site_point"] = site_id
    state["point_a"] = point["id"]
    deleted = api(a["admin"], "DELETE", f"/api/monitoring-points/{point['id']}?company_id={a['id']}")
    assert deleted.status_code == 200
    missing = api(a["admin"], "GET", f"/api/monitoring-points/{point['id']}?company_id={a['id']}")
    assert missing.status_code == 404


def test_labs_crud_and_lhu_evaluation_download_and_delete(state):
    a = state["a"]
    # Use a new point so this test remains independent from the CRUD deletion above.
    site = api(a["admin"], "POST", f"/api/sites?company_id={a['id']}", json={"name": f"{RUN_ID} LHU Site"})
    assert site.status_code == 200
    site_id = site.json()["id"]
    point_payload = {
        "site_id": site_id, "name": f"{RUN_ID} LHU Point", "jenis": "air_limbah", "frekuensi_bulan": 6,
        "tanggal_uji_terakhir": "2026-01-15",
        "parameters": [{"nama": "pH", "satuan": "-", "baku_mutu": 9.0, "baku_mutu_min": 6.0}],
    }
    point = api(a["admin"], "POST", f"/api/monitoring-points?company_id={a['id']}", json=point_payload)
    assert point.status_code == 200
    pid = point.json()["id"]
    lab = api(a["admin"], "POST", f"/api/labs?company_id={a['id']}", json={"nama": f"{RUN_ID} Lab", "akreditasi_kan": True, "narahubung": "Lab Contact"})
    assert lab.status_code == 200, lab.text
    lab_id = lab.json()["id"]
    labs = api(a["admin"], "GET", f"/api/labs?company_id={a['id']}")
    assert labs.status_code == 200 and any(x["id"] == lab_id for x in labs.json())
    lab_upd = api(a["admin"], "PUT", f"/api/labs/{lab_id}?company_id={a['id']}", json={"nama": f"{RUN_ID} Lab Updated", "akreditasi_kan": True, "narahubung": "Updated", "no_hp": "081", "catatan": ""})
    assert lab_upd.status_code == 200 and lab_upd.json()["nama"] == f"{RUN_ID} Lab Updated"

    def upload(test_date, value, filename):
        return api(a["admin"], "POST", f"/api/monitoring-points/{pid}/lhu?company_id={a['id']}", files={"file": (filename, b"%PDF-1.4 test file", "application/pdf")}, data={
            "periode": test_date[:7], "tanggal_uji": test_date, "lab_id": lab_id,
            "results": json.dumps([{"nama": "pH", "nilai": value, "satuan": "-", "baku_mutu": 9.0, "baku_mutu_min": 6.0}]),
        })

    first = upload("2026-02-15", "8.0", "first.pdf")
    assert first.status_code == 200, first.text
    assert first.json()["results"][0]["status"] == "sesuai"
    path = first.json()["storage_path"]
    second = upload("2026-03-15", "10.0", "second.pdf")
    assert second.status_code == 200, second.text
    assert second.json()["results"][0]["status"] == "melebihi"
    assert second.json()["tanggal_uji"] == "2026-03-15"
    point_after = api(a["admin"], "GET", f"/api/monitoring-points/{pid}?company_id={a['id']}" )
    assert point_after.status_code == 200 and point_after.json()["tanggal_uji_terakhir"] == "2026-03-15"
    assert point_after.json()["tanggal_jatuh_tempo_berikutnya"] == "2026-09-15"
    reports = api(a["admin"], "GET", f"/api/monitoring-points/{pid}/lhu?company_id={a['id']}")
    assert reports.status_code == 200
    rows = reports.json()
    assert [r["tanggal_uji"] for r in rows[:2]] == ["2026-03-15", "2026-02-15"]
    downloaded = api(a["admin"], "GET", f"/api/files/{path}")
    assert downloaded.status_code == 200 and downloaded.content == b"%PDF-1.4 test file"
    deleted = api(a["admin"], "DELETE", f"/api/lhu/{first.json()['id']}?company_id={a['id']}")
    assert deleted.status_code == 200
    third = upload("2026-03-20", "11.0", "third.pdf")
    assert third.status_code == 200, third.text
    assert third.json()["results"][0]["status"] == "melebihi"
    after = api(a["admin"], "GET", f"/api/monitoring-points/{pid}/lhu?company_id={a['id']}")
    assert after.status_code == 200 and not any(r["id"] == first.json()["id"] for r in after.json())
    deleted_lab = api(a["admin"], "DELETE", f"/api/labs/{lab_id}?company_id={a['id']}")
    assert deleted_lab.status_code == 200
    state["point_lhu_a"] = pid
    state["lhu_path_a"] = path
    state["lhu_report_a"] = second.json()["id"]


def test_dashboard_compliance_and_trend(state):
    a = state["a"]
    pid = state["point_lhu_a"]
    dashboard = api(a["admin"], "GET", f"/api/dashboard?company_id={a['id']}")
    assert dashboard.status_code == 200
    data = dashboard.json()
    assert all(k in data for k in ("overdue", "due_7", "due_14", "due_30", "compliance"))
    assert any(item["id"] == pid for item in data["overdue"])
    compliance = api(a["admin"], "GET", f"/api/compliance?company_id={a['id']}")
    assert compliance.status_code == 200
    c = compliance.json()
    assert isinstance(c["percent"], int) and c["total"] >= 1 and c["color"] in ("green", "yellow", "red")
    trend = api(a["admin"], "GET", f"/api/monitoring-points/{pid}/trend?parameter=pH&company_id={a['id']}")
    assert trend.status_code == 200
    t = trend.json()
    assert len(t["series"]) == 2 and t["series"][-1]["nilai"] == 11.0
    assert t["change_percent"] == 10.0 and t["perlu_perhatian"] is True and t["baku_mutu"] == 9.0


def test_settings_reminders_notifications_and_cron(state):
    swarna = state["swarna"]
    settings = api(swarna, "GET", "/api/settings/whatsapp")
    assert settings.status_code == 200
    assert "configured" in settings.json() and settings.json().get("api_key", "") in ("", "****")
    update = api(swarna, "PUT", "/api/settings/whatsapp", json={"enabled": True, "api_url": "https://wa.example.test/send", "api_key": "r1-secret-key", "sender_number": "081"})
    assert update.status_code == 200
    assert update.json()["api_key"] == "****" and update.json()["configured"] is True
    masked = api(swarna, "PUT", "/api/settings/whatsapp", json={"enabled": False, "api_url": "", "api_key": "****", "sender_number": ""})
    assert masked.status_code == 200
    assert masked.json()["api_key"] == "****"
    run = api(swarna, "POST", "/api/reminders/run-now")
    assert run.status_code == 200 and "emails_attempted" in run.json()
    logs = api(swarna, "GET", f"/api/notifications?company_id={state['a']['id']}")
    assert logs.status_code == 200
    no_auth = api(requests.Session(), "POST", "/api/cron/reminders")
    assert no_auth.status_code == 401
    secret = ""
    for line in Path("/app/backend/.env").read_text().splitlines():
        if line.startswith("WEBHOOK_CRON_SECRET="):
            secret = line.split("=", 1)[1].strip().strip('"')
    assert secret
    cron = api(requests.Session(), "POST", "/api/cron/reminders", headers={"Authorization": f"Bearer {secret}"})
    assert cron.status_code == 200 and cron.json().get("accepted") is True


def test_row_level_security_across_companies(state):
    a, b = state["a"], state["b"]
    # Make a B site/point/lab/report to test both reads and file isolation.
    site = api(b["admin"], "POST", f"/api/sites?company_id={b['id']}", json={"name": f"{RUN_ID} B Site"})
    assert site.status_code == 200
    sid = site.json()["id"]
    point = api(b["admin"], "POST", f"/api/monitoring-points?company_id={b['id']}", json={
        "site_id": sid, "name": f"{RUN_ID} B Point", "jenis": "emisi", "frekuensi_bulan": 6,
        "parameters": [{"nama": "SO2", "satuan": "mg/Nm3", "baku_mutu": 50.0}],
    })
    assert point.status_code == 200
    pid = point.json()["id"]
    lab = api(b["admin"], "POST", f"/api/labs?company_id={b['id']}", json={"nama": f"{RUN_ID} B Lab"})
    assert lab.status_code == 200
    lhu = api(b["admin"], "POST", f"/api/monitoring-points/{pid}/lhu?company_id={b['id']}", files={"file": ("b.pdf", b"B company file", "application/pdf")}, data={
        "periode": "2026-03", "tanggal_uji": "2026-03-01", "lab_id": lab.json()["id"],
        "results": json.dumps([{"nama": "SO2", "nilai": 20, "baku_mutu": 50}]),
    })
    assert lhu.status_code == 200, lhu.text
    bpath = lhu.json()["storage_path"]

    a_site = api(a["admin"], "POST", f"/api/sites?company_id={a['id']}", json={"name": f"{RUN_ID} A RLS Site"})
    assert a_site.status_code == 200
    a_site_id = a_site.json()["id"]
    a_point_create = api(a["admin"], "POST", f"/api/monitoring-points?company_id={a['id']}", json={
        "site_id": a_site_id, "name": f"{RUN_ID} A RLS Point", "jenis": "air_limbah", "frekuensi_bulan": 6,
        "parameters": [{"nama": "pH", "satuan": "-", "baku_mutu": 9.0}],
    })
    assert a_point_create.status_code == 200
    a_pid = a_point_create.json()["id"]

    # Updating an A point with a site ID owned by B must be rejected; this also
    # verifies that update validation preserves tenant boundaries for embedded refs.
    a_point = api(a["admin"], "GET", f"/api/monitoring-points/{a_pid}?company_id={a['id']}")
    assert a_point.status_code == 200
    a_body = a_point.json()
    cross_site_update = api(a["admin"], "PUT", f"/api/monitoring-points/{a_pid}?company_id={a['id']}", json={
        "site_id": sid, "name": a_body["name"], "jenis": a_body["jenis"],
        "frekuensi_bulan": a_body["frekuensi_bulan"], "tanggal_uji_terakhir": a_body.get("tanggal_uji_terakhir"),
        "parameters": a_body["parameters"],
    })
    cross_lab_upload = api(a["admin"], "POST", f"/api/monitoring-points/{a_pid}/lhu?company_id={a['id']}", files={"file": ("cross.pdf", b"cross-company lab", "application/pdf")}, data={
        "periode": "2026-04", "tanggal_uji": "2026-04-01", "lab_id": lab.json()["id"],
        "results": json.dumps([{"nama": "pH", "nilai": 7, "baku_mutu": 9}]),
    })
    assert cross_site_update.status_code == 400, cross_site_update.text
    assert cross_lab_upload.status_code == 400, cross_lab_upload.text

    for path in (
        f"/api/sites?company_id={b['id']}",
        f"/api/monitoring-points?company_id={b['id']}",
        f"/api/labs?company_id={b['id']}",
        f"/api/dashboard?company_id={b['id']}",
        f"/api/compliance?company_id={b['id']}",
        f"/api/notifications?company_id={b['id']}",
    ):
        response = api(a["admin"], "GET", path)
        assert response.status_code == 403, f"RLS GET unexpectedly allowed: {path} {response.text}"
    assert api(a["admin"], "GET", f"/api/monitoring-points/{pid}?company_id={b['id']}").status_code == 403
    assert api(a["admin"], "GET", f"/api/monitoring-points/{pid}/lhu?company_id={b['id']}").status_code == 403
    assert api(a["admin"], "GET", f"/api/files/{bpath}").status_code == 403
    assert api(a["admin"], "PUT", f"/api/sites/{sid}?company_id={b['id']}", json={"name": "Cross-company write", "address": ""}).status_code == 403
    assert api(a["admin"], "DELETE", f"/api/sites/{sid}?company_id={b['id']}").status_code == 403
    assert api(a["admin"], "PUT", f"/api/labs/{lab.json()['id']}?company_id={b['id']}", json={"nama": "Cross", "akreditasi_kan": False, "narahubung": "", "no_hp": "", "catatan": ""}).status_code == 403
    assert api(a["admin"], "DELETE", f"/api/labs/{lab.json()['id']}?company_id={b['id']}").status_code == 403
    assert api(a["admin"], "DELETE", f"/api/monitoring-points/{pid}?company_id={b['id']}").status_code == 403


def test_unauthorized_and_invalid_input_handling(state):
    no_auth = requests.Session()
    assert api(no_auth, "GET", "/api/dashboard").status_code == 401
    invalid = api(no_auth, "POST", "/api/auth/login", json={"email": ADMIN_EMAIL, "password": "wrong-password"})
    assert invalid.status_code == 401
    malformed = api(no_auth, "POST", "/api/auth/login", json={"email": "not-an-email", "password": "x"})
    assert malformed.status_code == 422



def test_brute_force_lockout_after_five_failures():
    """Auth hardening check: repeated bad passwords should trigger a lockout."""
    session = requests.Session()
    statuses = []
    for _ in range(6):
        response = api(session, "POST", "/api/auth/login", json={"email": ADMIN_EMAIL, "password": "definitely-wrong-r1"})
        statuses.append(response.status_code)
    assert statuses[-1] in (423, 429), f"No brute-force lockout after six failures: {statuses}"
