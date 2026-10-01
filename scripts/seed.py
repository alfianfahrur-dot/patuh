import io
import requests

BASE = "http://localhost:8001/api"

ADMIN = {"email": "alfianfahrur@gmail.com", "password": "SwarnaAdmin#2026"}
CLIENT_ADMIN_EMAIL = "budi.hrga@hijaulestari.co.id"


def jp(r):
    try:
        return r.json()
    except Exception:
        return r.text


def pdf_bytes(title):
    text = f"LHU - {title}"
    content = (
        "%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        "2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        "3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 120]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
        f"4 0 obj<</Length 70>>stream\nBT /F1 14 Tf 20 60 Td ({text}) Tj ET\nendstream endobj\n"
        "5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        "trailer<</Root 1 0 R>>\n%%EOF"
    )
    return content.encode("latin-1")


s = requests.Session()

# 1. admin login
tok = s.post(f"{BASE}/auth/login", json=ADMIN).json()["token"]
AH = {"Authorization": f"Bearer {tok}"}

# clean existing invite for client to allow re-run
existing = s.get(f"{BASE}/companies", headers=AH).json()
if any(c["name"] == "PT Hijau Lestari" for c in existing):
    print("Demo company already exists, skipping seed.")
    raise SystemExit(0)

# 2. create company + invite
comp = s.post(f"{BASE}/companies", headers=AH, json={
    "name": "PT Hijau Lestari", "admin_email": CLIENT_ADMIN_EMAIL, "admin_name": "Budi Santoso",
}).json()
print("company:", comp["company"]["name"])
invite_token = comp["invite_token"]

# 3. accept invite -> company admin
acc = s.post(f"{BASE}/invitations/accept", json={
    "token": invite_token, "name": "Budi Santoso", "password": "Budi#2026", "phone": "6281234500001",
}).json()
ctok = acc["token"]
company_id = acc["user"]["company_id"]
CH = {"Authorization": f"Bearer {ctok}"}
P = {"company_id": company_id}
print("client admin:", acc["user"]["email"], "company_id:", company_id)

# invite an HRGA teammate
s.post(f"{BASE}/invitations", headers=CH, params=P, json={
    "email": "siti.pic@hijaulestari.co.id", "role": "hrga", "name": "Siti Rahma"})

# 4. site
site = s.post(f"{BASE}/sites", headers=CH, params=P, json={
    "name": "Pabrik Cikarang", "address": "Kawasan Industri Jababeka, Cikarang"}).json()
sid = site["id"]

# 5. monitoring points
air_params = [
    {"nama": "pH", "satuan": "", "baku_mutu": 9, "baku_mutu_min": 6},
    {"nama": "BOD", "satuan": "mg/L", "baku_mutu": 30, "baku_mutu_min": None},
    {"nama": "COD", "satuan": "mg/L", "baku_mutu": 100, "baku_mutu_min": None},
    {"nama": "TSS", "satuan": "mg/L", "baku_mutu": 50, "baku_mutu_min": None},
]
emisi_params = [
    {"nama": "Partikulat", "satuan": "mg/Nm3", "baku_mutu": 230, "baku_mutu_min": None},
    {"nama": "SO2", "satuan": "mg/Nm3", "baku_mutu": 800, "baku_mutu_min": None},
]

p1 = s.post(f"{BASE}/monitoring-points", headers=CH, params=P, json={
    "site_id": sid, "name": "Outlet IPAL 1", "jenis": "air_limbah", "frekuensi_bulan": 6,
    "tanggal_uji_terakhir": "2026-04-10", "parameters": air_params}).json()
p2 = s.post(f"{BASE}/monitoring-points", headers=CH, params=P, json={
    "site_id": sid, "name": "Cerobong Boiler 2", "jenis": "emisi", "frekuensi_bulan": 6,
    "tanggal_uji_terakhir": "2026-02-01", "parameters": emisi_params}).json()
s.post(f"{BASE}/monitoring-points", headers=CH, params=P, json={
    "site_id": sid, "name": "Outlet IPAL 2", "jenis": "air_limbah", "frekuensi_bulan": 6,
    "tanggal_uji_terakhir": None, "parameters": air_params}).json()
print("points created")

# 6. labs
lab1 = s.post(f"{BASE}/labs", headers=CH, params=P, json={
    "nama": "Lab Sucofindo", "akreditasi_kan": True, "narahubung": "Pak Andi",
    "no_hp": "081298765432", "catatan": "Langganan utama, respon cepat"}).json()
s.post(f"{BASE}/labs", headers=CH, params=P, json={
    "nama": "Lab Enviro Mandiri", "akreditasi_kan": True, "narahubung": "Bu Dewi",
    "no_hp": "081233344455", "catatan": "Alternatif untuk emisi"})

# 7. LHU uploads for Outlet IPAL 1 (two periods -> trend)
def upload_lhu(point_id, periode, tanggal, lab_id, results):
    files = {"file": (f"{periode}.pdf", io.BytesIO(pdf_bytes(periode)), "application/pdf")}
    data = {"periode": periode, "tanggal_uji": tanggal, "lab_id": lab_id,
            "results": requests.compat.json.dumps(results)}
    r = s.post(f"{BASE}/monitoring-points/{point_id}/lhu", headers=CH, params=P, files=files, data=data)
    print("lhu", periode, r.status_code)

upload_lhu(p1["id"], "Semester 2 2025", "2025-10-05", lab1["id"], [
    {"nama": "pH", "satuan": "", "baku_mutu": 9, "baku_mutu_min": 6, "nilai": 7.2},
    {"nama": "BOD", "satuan": "mg/L", "baku_mutu": 30, "baku_mutu_min": None, "nilai": 16},
    {"nama": "COD", "satuan": "mg/L", "baku_mutu": 100, "baku_mutu_min": None, "nilai": 65},
    {"nama": "TSS", "satuan": "mg/L", "baku_mutu": 50, "baku_mutu_min": None, "nilai": 28},
])
upload_lhu(p1["id"], "Semester 1 2026", "2026-04-10", lab1["id"], [
    {"nama": "pH", "satuan": "", "baku_mutu": 9, "baku_mutu_min": 6, "nilai": 7.6},
    {"nama": "BOD", "satuan": "mg/L", "baku_mutu": 30, "baku_mutu_min": None, "nilai": 26},
    {"nama": "COD", "satuan": "mg/L", "baku_mutu": 100, "baku_mutu_min": None, "nilai": 92},
    {"nama": "TSS", "satuan": "mg/L", "baku_mutu": 50, "baku_mutu_min": None, "nilai": 44},
])

print("SEED DONE")
