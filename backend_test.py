#!/usr/bin/env python3
"""
Backend API test for PATUH Baku Mutu endpoints.
Tests seed idempotency, search, suggestions, apply, evaluation, and admin verification.
"""
import requests
import json
import sys
import io
from typing import Optional

# Base URL from frontend/.env
BASE_URL = "https://gh-sync-20.preview.emergentagent.com/api"

# Test credentials
ADMIN_EMAIL = "alfianfahrur@gmail.com"
ADMIN_PASSWORD = "SwarnaAdmin#2026"

# Global token storage
token: Optional[str] = None
company_id: Optional[str] = None
site_id: Optional[str] = None
point_id: Optional[str] = None


def log(msg: str):
    """Print test log message."""
    print(f"[TEST] {msg}")


def fail(msg: str):
    """Print failure and exit."""
    print(f"[FAIL] {msg}")
    sys.exit(1)


def auth_headers():
    """Return Authorization header with bearer token."""
    if not token:
        fail("No token available. Login first.")
    return {"Authorization": f"Bearer {token}"}


def test_login():
    """Test case: Login as swarna_admin."""
    global token
    log("Test 1: Login as swarna_admin")
    
    resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30
    )
    
    if resp.status_code != 200:
        fail(f"Login failed with status {resp.status_code}: {resp.text}")
    
    data = resp.json()
    if "token" not in data:
        fail(f"Login response missing token: {data}")
    
    token = data["token"]
    log(f"✅ Login successful, token obtained")


def test_seed_idempotency():
    """Test case 1: Seed idempotency - call twice, verify totals."""
    log("Test 2: Seed idempotency (POST /api/admin/baku-mutu/seed)")
    
    # First seed
    resp1 = requests.post(
        f"{BASE_URL}/admin/baku-mutu/seed",
        headers=auth_headers(),
        timeout=30
    )
    
    if resp1.status_code != 200:
        fail(f"First seed failed with status {resp1.status_code}: {resp1.text}")
    
    data1 = resp1.json()
    log(f"First seed response: {json.dumps(data1, indent=2)}")
    
    # Check totals
    if data1.get("total_regulasi") != 6:
        fail(f"Expected total_regulasi=6, got {data1.get('total_regulasi')}")
    
    if data1.get("total_standar") != 108:
        fail(f"Expected total_standar=108, got {data1.get('total_standar')}")
    
    # First run should have either standar_ditambah=108 or standar_diubah=108
    added = data1.get("standar_ditambah", 0)
    updated = data1.get("standar_diubah", 0)
    if added + updated != 108:
        fail(f"Expected standar_ditambah + standar_diubah = 108, got {added} + {updated}")
    
    log(f"✅ First seed: total_regulasi=6, total_standar=108, standar_ditambah={added}, standar_diubah={updated}")
    
    # Second seed (idempotency check)
    resp2 = requests.post(
        f"{BASE_URL}/admin/baku-mutu/seed",
        headers=auth_headers(),
        timeout=30
    )
    
    if resp2.status_code != 200:
        fail(f"Second seed failed with status {resp2.status_code}: {resp2.text}")
    
    data2 = resp2.json()
    log(f"Second seed response: {json.dumps(data2, indent=2)}")
    
    # Totals should remain the same
    if data2.get("total_regulasi") != 6:
        fail(f"Second seed: Expected total_regulasi=6, got {data2.get('total_regulasi')}")
    
    if data2.get("total_standar") != 108:
        fail(f"Second seed: Expected total_standar=108, got {data2.get('total_standar')}")
    
    # Second run should report *_diubah counts (no new additions)
    if data2.get("standar_ditambah", 0) > 0:
        log(f"⚠️  Warning: Second seed added {data2.get('standar_ditambah')} new standards (expected 0)")
    
    log(f"✅ Second seed idempotent: totals remain 6/108, no duplicates")


def test_search():
    """Test case 2: Search standards."""
    log("Test 3: Search standards (GET /api/baku-mutu/standar?kategori=air_limbah&q=hotel)")
    
    resp = requests.get(
        f"{BASE_URL}/baku-mutu/standar",
        params={"kategori": "air_limbah", "q": "hotel"},
        headers=auth_headers(),
        timeout=30
    )
    
    if resp.status_code != 200:
        fail(f"Search failed with status {resp.status_code}: {resp.text}")
    
    data = resp.json()
    
    if not isinstance(data, list):
        fail(f"Expected list response, got {type(data)}")
    
    if len(data) == 0:
        fail("Search returned empty list, expected non-empty results for 'hotel'")
    
    log(f"✅ Search returned {len(data)} results")
    
    # Check first item structure
    first = data[0]
    if "regulasi" not in first:
        fail(f"First result missing 'regulasi' field: {first}")
    
    if "status" not in first["regulasi"]:
        fail(f"First result regulasi missing 'status' field: {first['regulasi']}")
    
    if "perlu_verifikasi" not in first:
        fail(f"First result missing 'perlu_verifikasi' field: {first}")
    
    log(f"✅ First result has regulasi.status='{first['regulasi']['status']}', perlu_verifikasi={first['perlu_verifikasi']}")


def test_suggestions_debit_variants():
    """Test case 3: Suggestions with debit variants."""
    log("Test 4: Suggestions with debit variants")
    
    # Test 3a: debit=120 (should get > 50 variant)
    log("Test 4a: GET /api/baku-mutu/saran?kategori=air_limbah&q=hotel&debit=120")
    resp1 = requests.get(
        f"{BASE_URL}/baku-mutu/saran",
        params={"kategori": "air_limbah", "q": "hotel", "debit": 120},
        headers=auth_headers(),
        timeout=30
    )
    
    if resp1.status_code != 200:
        fail(f"Suggestions (debit=120) failed with status {resp1.status_code}: {resp1.text}")
    
    data1 = resp1.json()
    
    if "hasil" not in data1:
        fail(f"Response missing 'hasil' field: {data1}")
    
    if "perlu_pilih_varian" not in data1:
        fail(f"Response missing 'perlu_pilih_varian' field: {data1}")
    
    if "jumlah" not in data1:
        fail(f"Response missing 'jumlah' field: {data1}")
    
    if data1["perlu_pilih_varian"] is not False:
        fail(f"Expected perlu_pilih_varian=false for debit=120, got {data1['perlu_pilih_varian']}")
    
    if len(data1["hasil"]) == 0:
        fail("Expected non-empty hasil for hotel + debit=120")
    
    first1 = data1["hasil"][0]
    sub_kat1 = first1.get("sub_kategori", "")
    
    if "> 50" not in sub_kat1:
        fail(f"Expected first result sub_kategori to contain '> 50', got: {sub_kat1}")
    
    if not first1.get("alasan_cocok"):
        fail(f"Expected non-empty alasan_cocok, got: {first1.get('alasan_cocok')}")
    
    if first1.get("perlu_verifikasi") is not True:
        fail(f"Expected perlu_verifikasi=true for first result, got {first1.get('perlu_verifikasi')}")
    
    log(f"✅ debit=120: first result sub_kategori contains '> 50', alasan_cocok present, perlu_verifikasi=true")
    
    # Test 3b: debit=2 (should get <= 3 variant)
    log("Test 4b: GET /api/baku-mutu/saran?kategori=air_limbah&q=hotel&debit=2")
    resp2 = requests.get(
        f"{BASE_URL}/baku-mutu/saran",
        params={"kategori": "air_limbah", "q": "hotel", "debit": 2},
        headers=auth_headers(),
        timeout=30
    )
    
    if resp2.status_code != 200:
        fail(f"Suggestions (debit=2) failed with status {resp2.status_code}: {resp2.text}")
    
    data2 = resp2.json()
    
    if len(data2["hasil"]) == 0:
        fail("Expected non-empty hasil for hotel + debit=2")
    
    first2 = data2["hasil"][0]
    sub_kat2 = first2.get("sub_kategori", "")
    
    if "<= 3" not in sub_kat2 and "≤ 3" not in sub_kat2:
        fail(f"Expected first result sub_kategori to reference '<= 3' variant, got: {sub_kat2}")
    
    log(f"✅ debit=2: first result sub_kategori references '<= 3' variant")
    
    # Test 3c: tekstil + debit=500 (should get 100 - 1.000 variant)
    log("Test 4c: GET /api/baku-mutu/saran?kategori=air_limbah&q=tekstil&debit=500")
    resp3 = requests.get(
        f"{BASE_URL}/baku-mutu/saran",
        params={"kategori": "air_limbah", "q": "tekstil", "debit": 500},
        headers=auth_headers(),
        timeout=30
    )
    
    if resp3.status_code != 200:
        fail(f"Suggestions (tekstil debit=500) failed with status {resp3.status_code}: {resp3.text}")
    
    data3 = resp3.json()
    
    if len(data3["hasil"]) == 0:
        fail("Expected non-empty hasil for tekstil + debit=500")
    
    first3 = data3["hasil"][0]
    sub_kat3 = first3.get("sub_kategori", "")
    
    if "100 - 1.000" not in sub_kat3 and "100-1.000" not in sub_kat3 and "100 - 1000" not in sub_kat3:
        fail(f"Expected first result sub_kategori to contain '100 - 1.000', got: {sub_kat3}")
    
    log(f"✅ tekstil debit=500: first result sub_kategori contains '100 - 1.000' range")
    
    # Test 3d: hotel without debit (should have perlu_pilih_varian=true)
    log("Test 4d: GET /api/baku-mutu/saran?kategori=air_limbah&q=hotel (no debit)")
    resp4 = requests.get(
        f"{BASE_URL}/baku-mutu/saran",
        params={"kategori": "air_limbah", "q": "hotel"},
        headers=auth_headers(),
        timeout=30
    )
    
    if resp4.status_code != 200:
        fail(f"Suggestions (hotel no debit) failed with status {resp4.status_code}: {resp4.text}")
    
    data4 = resp4.json()
    
    if data4.get("perlu_pilih_varian") is not True:
        fail(f"Expected perlu_pilih_varian=true when no debit given, got {data4.get('perlu_pilih_varian')}")
    
    # All returned items should have skor > 0 (zero-signal items hidden when q given)
    for item in data4["hasil"]:
        if item.get("skor", 0) <= 0:
            fail(f"Expected all items to have skor > 0 when q given, found item with skor={item.get('skor')}")
    
    log(f"✅ hotel (no debit): perlu_pilih_varian=true, all items have skor > 0")


def test_apply_and_evaluation():
    """Test case 4: Apply standard + LHU evaluation."""
    global company_id, site_id, point_id
    
    log("Test 5: Apply standard + evaluation")
    
    # Create company
    log("Test 5a: Create company (POST /api/companies)")
    resp_comp = requests.post(
        f"{BASE_URL}/companies",
        json={"name": "PT Uji Baku Mutu", "admin_email": "uji.bakumutu@example.com"},
        headers=auth_headers(),
        timeout=30
    )
    
    if resp_comp.status_code != 200:
        fail(f"Create company failed with status {resp_comp.status_code}: {resp_comp.text}")
    
    comp_data = resp_comp.json()
    company_id = comp_data.get("company", {}).get("id")
    
    if not company_id:
        fail(f"Company creation response missing company.id: {comp_data}")
    
    log(f"✅ Company created: {company_id}")
    
    # Create site
    log("Test 5b: Create site (POST /api/sites?company_id=...)")
    resp_site = requests.post(
        f"{BASE_URL}/sites",
        params={"company_id": company_id},
        json={"name": "Pabrik Uji", "address": ""},
        headers=auth_headers(),
        timeout=30
    )
    
    if resp_site.status_code != 200:
        fail(f"Create site failed with status {resp_site.status_code}: {resp_site.text}")
    
    site_data = resp_site.json()
    site_id = site_data.get("id")
    
    if not site_id:
        fail(f"Site creation response missing id: {site_data}")
    
    log(f"✅ Site created: {site_id}")
    
    # Create monitoring point
    log("Test 5c: Create monitoring point (POST /api/monitoring-points?company_id=...)")
    resp_point = requests.post(
        f"{BASE_URL}/monitoring-points",
        params={"company_id": company_id},
        json={
            "site_id": site_id,
            "name": "Outlet IPAL Uji",
            "jenis": "air_limbah",
            "frekuensi_bulan": 6,
            "parameters": []
        },
        headers=auth_headers(),
        timeout=30
    )
    
    if resp_point.status_code != 200:
        fail(f"Create monitoring point failed with status {resp_point.status_code}: {resp_point.text}")
    
    point_data = resp_point.json()
    point_id = point_data.get("id")
    
    if not point_id:
        fail(f"Monitoring point creation response missing id: {point_data}")
    
    log(f"✅ Monitoring point created: {point_id}")
    
    # Apply standard
    log("Test 5d: Apply standard (POST /api/titik/{point_id}/terapkan-baku-mutu?company_id=...)")
    resp_apply = requests.post(
        f"{BASE_URL}/titik/{point_id}/terapkan-baku-mutu",
        params={"company_id": company_id},
        json={"standar_id": "AL-DOM-NK-MA-GT50"},
        headers=auth_headers(),
        timeout=30
    )
    
    if resp_apply.status_code != 200:
        fail(f"Apply standard failed with status {resp_apply.status_code}: {resp_apply.text}")
    
    apply_data = resp_apply.json()
    log(f"✅ Standard applied")
    
    # Get monitoring point to verify
    log("Test 5e: Verify applied standard (GET /api/monitoring-points/{point_id}?company_id=...)")
    resp_get = requests.get(
        f"{BASE_URL}/monitoring-points/{point_id}",
        params={"company_id": company_id},
        headers=auth_headers(),
        timeout=30
    )
    
    if resp_get.status_code != 200:
        fail(f"Get monitoring point failed with status {resp_get.status_code}: {resp_get.text}")
    
    point_verify = resp_get.json()
    
    # Verify standar_id
    if point_verify.get("standar_id") != "AL-DOM-NK-MA-GT50":
        fail(f"Expected standar_id='AL-DOM-NK-MA-GT50', got {point_verify.get('standar_id')}")
    
    # Verify sumber_baku_mutu
    if point_verify.get("sumber_baku_mutu") != "saran_otomatis":
        fail(f"Expected sumber_baku_mutu='saran_otomatis', got {point_verify.get('sumber_baku_mutu')}")
    
    # Verify snapshot_standar present
    if "snapshot_standar" not in point_verify:
        fail(f"Expected snapshot_standar field, not found")
    
    # Verify parameters
    params = point_verify.get("parameters", [])
    if not params:
        fail("Expected non-empty parameters after applying standard")
    
    # Find pH parameter (tipe=rentang, min=6, maks=9)
    ph_param = next((p for p in params if p.get("kode") == "pH"), None)
    if not ph_param:
        fail("Expected pH parameter with kode='pH'")
    
    if ph_param.get("tipe") != "rentang":
        fail(f"Expected pH tipe='rentang', got {ph_param.get('tipe')}")
    
    if ph_param.get("baku_mutu_min") != 6:
        fail(f"Expected pH baku_mutu_min=6, got {ph_param.get('baku_mutu_min')}")
    
    if ph_param.get("baku_mutu") != 9:
        fail(f"Expected pH baku_mutu=9, got {ph_param.get('baku_mutu')}")
    
    log(f"✅ pH parameter verified: tipe=rentang, min=6, maks=9")
    
    # Find BOD5 parameter (tipe=maks, maks=30)
    bod_param = next((p for p in params if p.get("kode") == "BOD5"), None)
    if not bod_param:
        fail("Expected BOD5 parameter with kode='BOD5'")
    
    if bod_param.get("tipe") != "maks":
        fail(f"Expected BOD5 tipe='maks', got {bod_param.get('tipe')}")
    
    if bod_param.get("baku_mutu") != 30:
        fail(f"Expected BOD5 baku_mutu=30, got {bod_param.get('baku_mutu')}")
    
    log(f"✅ BOD5 parameter verified: tipe=maks, maks=30")
    
    # Upload LHU
    log("Test 5f: Upload LHU (POST /api/monitoring-points/{point_id}/lhu?company_id=...)")
    
    # Create a small dummy file
    dummy_file = io.BytesIO(b"Test LHU file content")
    
    results_json = json.dumps([
        {"nama": "BOD5", "nilai": 28},
        {"nama": "pH", "nilai": 11},
        {"nama": "Fecal coliform", "nilai": "< LOQ"}
    ])
    
    files = {"file": ("test_lhu.txt", dummy_file, "text/plain")}
    data = {
        "periode": "2026-Q1",
        "tanggal_uji": "2026-01-15",
        "lab_id": "",
        "results": results_json
    }
    
    resp_lhu = requests.post(
        f"{BASE_URL}/monitoring-points/{point_id}/lhu",
        params={"company_id": company_id},
        headers=auth_headers(),
        files=files,
        data=data,
        timeout=30
    )
    
    if resp_lhu.status_code != 200:
        fail(f"Upload LHU failed with status {resp_lhu.status_code}: {resp_lhu.text}")
    
    lhu_data = resp_lhu.json()
    
    # Verify evaluation results
    results = lhu_data.get("results", [])
    if not results:
        fail("Expected non-empty results in LHU response")
    
    log(f"✅ LHU uploaded, evaluating {len(results)} parameters")
    
    # Find BOD5 result (should be "mendekati" since 28 >= 0.8*30=24)
    bod_result = next((r for r in results if r.get("nama") == "BOD5"), None)
    if not bod_result:
        fail("Expected BOD5 in LHU results")
    
    if bod_result.get("status") != "mendekati":
        fail(f"Expected BOD5 status='mendekati' (28 >= 0.8*30), got {bod_result.get('status')}")
    
    log(f"✅ BOD5 evaluation: status='mendekati' (28 >= 24)")
    
    # Find pH result (should be "melebihi" since 11 is outside 6-9 range)
    ph_result = next((r for r in results if r.get("nama") == "pH"), None)
    if not ph_result:
        fail("Expected pH in LHU results")
    
    if ph_result.get("status") != "melebihi":
        fail(f"Expected pH status='melebihi' (11 outside 6-9), got {ph_result.get('status')}")
    
    log(f"✅ pH evaluation: status='melebihi' (11 outside 6-9 range)")
    
    # Find Fecal coliform result (should be "sesuai" since < LOQ treated as below detection)
    fc_result = next((r for r in results if r.get("nama") == "Fecal coliform"), None)
    if not fc_result:
        fail("Expected Fecal coliform in LHU results")
    
    if fc_result.get("status") != "sesuai":
        fail(f"Expected Fecal coliform status='sesuai' (< LOQ), got {fc_result.get('status')}")
    
    log(f"✅ Fecal coliform evaluation: status='sesuai' (< LOQ treated as below detection)")


def test_admin_verify_and_audit():
    """Test case 5: Admin verify + audit."""
    log("Test 6: Admin verify + audit")
    
    # Pick a standard with perlu_verifikasi=true (AL-DOM-NK-MA-GT50)
    standar_id = "AL-DOM-NK-MA-GT50"
    
    log(f"Test 6a: Verify standard (POST /api/admin/baku-mutu/standar/{standar_id}/verifikasi)")
    resp_verify = requests.post(
        f"{BASE_URL}/admin/baku-mutu/standar/{standar_id}/verifikasi",
        headers=auth_headers(),
        timeout=30
    )
    
    if resp_verify.status_code != 200:
        fail(f"Verify standard failed with status {resp_verify.status_code}: {resp_verify.text}")
    
    verify_data = resp_verify.json()
    
    # Check diverifikasi_pada is set
    if not verify_data.get("diverifikasi_pada"):
        fail(f"Expected diverifikasi_pada to be set, got {verify_data.get('diverifikasi_pada')}")
    
    # Check perlu_verifikasi is false
    if verify_data.get("perlu_verifikasi") is not False:
        fail(f"Expected perlu_verifikasi=false after verification, got {verify_data.get('perlu_verifikasi')}")
    
    log(f"✅ Standard verified: diverifikasi_pada set, perlu_verifikasi=false")
    
    # Get audit log
    log("Test 6b: Get audit log (GET /api/admin/baku-mutu/audit)")
    resp_audit = requests.get(
        f"{BASE_URL}/admin/baku-mutu/audit",
        headers=auth_headers(),
        timeout=30
    )
    
    if resp_audit.status_code != 200:
        fail(f"Get audit log failed with status {resp_audit.status_code}: {resp_audit.text}")
    
    audit_data = resp_audit.json()
    
    if not isinstance(audit_data, list):
        fail(f"Expected audit log to be a list, got {type(audit_data)}")
    
    # Find verification entry for our standard
    verify_entry = next((e for e in audit_data if e.get("standar_id") == standar_id and e.get("aksi") == "verifikasi"), None)
    
    if not verify_entry:
        fail(f"Expected audit entry with aksi='verifikasi' for standar_id={standar_id}")
    
    log(f"✅ Audit log contains verification entry for {standar_id}")


def main():
    """Run all tests."""
    print("=" * 80)
    print("PATUH Baku Mutu Backend API Tests")
    print("=" * 80)
    
    try:
        test_login()
        test_seed_idempotency()
        test_search()
        test_suggestions_debit_variants()
        test_apply_and_evaluation()
        test_admin_verify_and_audit()
        
        print("=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        sys.exit(0)
        
    except Exception as e:
        print("=" * 80)
        print(f"❌ TEST SUITE FAILED: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
