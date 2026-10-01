import os
import json
import uuid
import hmac
import asyncio
import logging
import calendar
from datetime import datetime, timezone, date, timedelta
from typing import Optional, List

from fastapi import (
    FastAPI, APIRouter, Request, HTTPException, Depends,
    UploadFile, File, Form, BackgroundTasks, Response, Query, Header,
)
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

from db import db, client
from auth_utils import hash_password, verify_password, create_access_token, decode_token
import storage_service as storage
import email_service as mailer

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()
api = APIRouter(prefix="/api")

SWARNA_ADMIN = "swarna_admin"
COMPANY_ADMIN = "company_admin"
HRGA = "hrga"
SUPERVISOR = "supervisor"

ROLE_LABELS = {
    SWARNA_ADMIN: "Admin Swarna",
    COMPANY_ADMIN: "Admin Perusahaan",
    HRGA: "HRGA / PIC Lingkungan",
    SUPERVISOR: "Supervisor",
}

REMINDER_THRESHOLDS = [30, 14, 7, 0]


# ----------------------------- helpers -----------------------------
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id() -> str:
    return str(uuid.uuid4())


def add_months(d: date, months: int) -> date:
    m = d.month - 1 + months
    y = d.year + m // 12
    m = m % 12 + 1
    day = min(d.day, calendar.monthrange(y, m)[1])
    return date(y, m, day)


def compute_due(last_test: Optional[str], freq_months: int) -> Optional[str]:
    if not last_test:
        return None
    try:
        d = date.fromisoformat(last_test)
    except Exception:
        return None
    return add_months(d, freq_months).isoformat()


def clean(doc: dict) -> dict:
    doc.pop("_id", None)
    return doc


# ----------------------------- auth deps -----------------------------
async def get_current_user(request: Request) -> dict:
    token = None
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
    if not token:
        token = request.query_params.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Tidak terautentikasi")
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Sesi tidak valid atau kedaluwarsa")
    user = await db.users.find_one({"id": payload.get("sub")}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Pengguna tidak ditemukan")
    return user


async def get_accessible_company_ids(user: dict) -> List[str]:
    if user["role"] == SWARNA_ADMIN:
        rows = await db.assignments.find({"swarna_user_id": user["id"]}, {"_id": 0, "company_id": 1}).to_list(1000)
        return [r["company_id"] for r in rows]
    if user.get("company_id"):
        return [user["company_id"]]
    return []


async def get_company_id(request: Request, user: dict = Depends(get_current_user)) -> str:
    accessible = await get_accessible_company_ids(user)
    requested = request.query_params.get("company_id")
    if requested:
        if requested not in accessible:
            raise HTTPException(status_code=403, detail="Anda tidak punya akses ke perusahaan ini")
        return requested
    if accessible:
        return accessible[0]
    raise HTTPException(status_code=400, detail="Belum ada perusahaan yang dapat diakses")


def require_roles(*roles):
    async def dep(user: dict = Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Peran Anda tidak diizinkan untuk aksi ini")
        return user
    return dep


# ----------------------------- models -----------------------------
class LoginBody(BaseModel):
    email: EmailStr
    password: str


class AcceptInviteBody(BaseModel):
    token: str
    name: str
    password: str
    phone: Optional[str] = ""


class CompanyCreate(BaseModel):
    name: str
    admin_email: EmailStr
    admin_name: Optional[str] = ""


class InviteCreate(BaseModel):
    email: EmailStr
    role: str
    name: Optional[str] = ""


class SiteBody(BaseModel):
    name: str
    address: Optional[str] = ""


class ParameterBody(BaseModel):
    nama: str
    satuan: str = ""
    baku_mutu: Optional[float] = None
    baku_mutu_min: Optional[float] = None


class MonitoringPointBody(BaseModel):
    site_id: str
    name: str
    jenis: str  # air_limbah | emisi
    frekuensi_bulan: int = 6
    tanggal_uji_terakhir: Optional[str] = None
    parameters: List[ParameterBody] = []


class LabBody(BaseModel):
    nama: str
    akreditasi_kan: bool = False
    narahubung: Optional[str] = ""
    no_hp: Optional[str] = ""
    catatan: Optional[str] = ""


class WhatsAppConfigBody(BaseModel):
    enabled: bool = False
    api_url: Optional[str] = ""
    api_key: Optional[str] = ""
    sender_number: Optional[str] = ""


class RegisterCompanyBody(BaseModel):
    company_name: str
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = ""


class EmailOnlyBody(BaseModel):
    email: EmailStr


def _new_verification_token() -> str:
    return new_id() + new_id().replace("-", "")


async def _send_verification_email(email: str, name: str, token: str):
    try:
        await mailer.send_email(
            to=email,
            subject="Verifikasi email Anda - Swarna PROPER Tracker",
            html=mailer.verification_html(name, token),
        )
        status, msg = "terkirim", "Email verifikasi"
    except Exception as e:
        logger.error(f"Verification email failed: {e}")
        status, msg = "gagal", str(e)
    await db.notification_log.insert_one({
        "id": new_id(), "company_id": None, "type": "verification", "recipient_email": email,
        "channel": "email", "status": status, "sent_at": now_iso(), "message": msg,
    })


# ----------------------------- auth routes -----------------------------
@api.post("/auth/register-company")
async def register_company(body: RegisterCompanyBody, bg: BackgroundTasks):
    email = body.email.lower().strip()
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Kata sandi minimal 6 karakter")
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=409, detail="Email sudah terdaftar. Silakan masuk.")
    company = {
        "id": new_id(),
        "name": body.company_name,
        "status_pendaftaran": "menunggu_verifikasi",
        "metode_masuk": "self_signup",
        "created_at": now_iso(),
        "created_by": None,
    }
    await db.companies.insert_one(company)
    user = {
        "id": new_id(),
        "email": email,
        "password_hash": hash_password(body.password),
        "name": body.name,
        "phone": body.phone or "",
        "role": COMPANY_ADMIN,
        "company_id": company["id"],
        "email_verified": False,
        "created_at": now_iso(),
    }
    await db.users.insert_one(user)
    vtoken = _new_verification_token()
    await db.email_verifications.insert_one({
        "id": new_id(), "email": email, "user_id": user["id"], "token": vtoken, "used": False,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(), "created_at": now_iso(),
    })
    bg.add_task(_send_verification_email, email, body.name, vtoken)
    return {"status": "verification_sent", "email": email}


@api.get("/auth/verify-email/{token}")
async def verify_email(token: str):
    rec = await db.email_verifications.find_one({"token": token})
    if not rec or rec.get("used"):
        raise HTTPException(status_code=404, detail="Tautan verifikasi tidak ditemukan atau sudah dipakai")
    if datetime.fromisoformat(rec["expires_at"]) < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Tautan verifikasi sudah kedaluwarsa. Minta kirim ulang.")
    user = await db.users.find_one({"id": rec["user_id"]})
    if not user:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan")
    await db.users.update_one({"id": user["id"]}, {"$set": {"email_verified": True}})
    await db.companies.update_one({"id": user["company_id"], "status_pendaftaran": "menunggu_verifikasi"},
                                  {"$set": {"status_pendaftaran": "aktif"}})
    await db.email_verifications.update_one({"id": rec["id"]}, {"$set": {"used": True, "used_at": now_iso()}})
    jwt_token = create_access_token(user["id"], user["email"])
    return {"token": jwt_token, "user": {k: v for k, v in user.items() if k not in ("_id", "password_hash")}}


@api.post("/auth/resend-verification")
async def resend_verification(body: EmailOnlyBody, bg: BackgroundTasks):
    email = body.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if user and user.get("email_verified") is False:
        vtoken = _new_verification_token()
        await db.email_verifications.insert_one({
            "id": new_id(), "email": email, "user_id": user["id"], "token": vtoken, "used": False,
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(), "created_at": now_iso(),
        })
        bg.add_task(_send_verification_email, email, user.get("name", ""), vtoken)
    return {"status": "ok"}


@api.post("/auth/login")
async def login(body: LoginBody, request: Request):
    email = body.email.lower().strip()
    ip = request.client.host if request.client else "unknown"
    identifier = f"{ip}:{email}"
    now = datetime.now(timezone.utc)
    rec = await db.login_attempts.find_one({"identifier": identifier})
    if rec and rec.get("locked_until") and datetime.fromisoformat(rec["locked_until"]) > now:
        raise HTTPException(status_code=429, detail="Terlalu banyak percobaan gagal. Coba lagi dalam 15 menit.")
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(body.password, user.get("password_hash", "")):
        count = (rec.get("count", 0) if rec else 0) + 1
        update = {"identifier": identifier, "count": count, "last_attempt": now.isoformat()}
        if count >= 5:
            update["locked_until"] = (now + timedelta(minutes=15)).isoformat()
            update["count"] = 0
        await db.login_attempts.update_one({"identifier": identifier}, {"$set": update}, upsert=True)
        raise HTTPException(status_code=401, detail="Email atau kata sandi salah")
    await db.login_attempts.delete_one({"identifier": identifier})
    if user.get("email_verified") is False:
        raise HTTPException(status_code=403, detail="Email belum diverifikasi. Cek kotak masuk Anda untuk tautan verifikasi.")
    token = create_access_token(user["id"], user["email"])
    safe = {k: v for k, v in user.items() if k not in ("_id", "password_hash")}
    return {"token": token, "user": safe}


@api.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return user


@api.post("/auth/logout")
async def logout(user: dict = Depends(get_current_user)):
    return {"ok": True}


@api.get("/invitations/validate/{token}")
async def validate_invite(token: str):
    inv = await db.invitations.find_one({"token": token}, {"_id": 0})
    if not inv or inv.get("used"):
        raise HTTPException(status_code=404, detail="Undangan tidak ditemukan atau sudah dipakai")
    if datetime.fromisoformat(inv["expires_at"]) < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Undangan sudah kedaluwarsa")
    company = await db.companies.find_one({"id": inv["company_id"]}, {"_id": 0})
    return {
        "email": inv["email"],
        "role": inv["role"],
        "role_label": ROLE_LABELS.get(inv["role"], inv["role"]),
        "company_name": company["name"] if company else "",
    }


@api.post("/invitations/accept")
async def accept_invite(body: AcceptInviteBody):
    inv = await db.invitations.find_one({"token": body.token})
    if not inv or inv.get("used"):
        raise HTTPException(status_code=404, detail="Undangan tidak ditemukan atau sudah dipakai")
    if datetime.fromisoformat(inv["expires_at"]) < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Undangan sudah kedaluwarsa")
    existing = await db.users.find_one({"email": inv["email"]})
    if existing:
        raise HTTPException(status_code=409, detail="Akun dengan email ini sudah ada")
    user = {
        "id": new_id(),
        "email": inv["email"],
        "password_hash": hash_password(body.password),
        "name": body.name,
        "phone": body.phone or "",
        "role": inv["role"],
        "company_id": inv["company_id"],
        "email_verified": True,
        "created_at": now_iso(),
    }
    await db.users.insert_one(user)
    await db.invitations.update_one({"id": inv["id"]}, {"$set": {"used": True, "used_at": now_iso()}})
    await db.companies.update_one({"id": inv["company_id"], "status_pendaftaran": "diundang"},
                                  {"$set": {"status_pendaftaran": "aktif"}})
    token = create_access_token(user["id"], user["email"])
    return {"token": token, "user": {k: v for k, v in user.items() if k not in ("_id", "password_hash")}}


# ----------------------------- companies & assignments -----------------------------
@api.post("/companies")
async def create_company(body: CompanyCreate, bg: BackgroundTasks, user: dict = Depends(require_roles(SWARNA_ADMIN))):
    admin_email = body.admin_email.lower().strip()
    if await db.users.find_one({"email": admin_email}):
        raise HTTPException(status_code=409, detail="Email admin klien sudah terdaftar")
    company = {
        "id": new_id(),
        "name": body.name,
        "status_pendaftaran": "diundang",
        "metode_masuk": "undangan",
        "created_at": now_iso(),
        "created_by": user["id"],
    }
    await db.companies.insert_one(company)
    await db.assignments.insert_one({
        "id": new_id(), "swarna_user_id": user["id"], "company_id": company["id"], "created_at": now_iso(),
    })
    token = new_id() + new_id().replace("-", "")
    inv = {
        "id": new_id(),
        "company_id": company["id"],
        "email": admin_email,
        "name": body.admin_name or "",
        "role": COMPANY_ADMIN,
        "token": token,
        "used": False,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "created_at": now_iso(),
    }
    await db.invitations.insert_one(inv)
    bg.add_task(_send_invite_email, admin_email, body.name, COMPANY_ADMIN, token)
    return {"company": clean(company), "invite_token": token,
            "invite_link": f"{mailer.APP_BASE_URL}/invite/{token}"}


async def _send_invite_email(email: str, company_name: str, role: str, token: str):
    try:
        await mailer.send_email(
            to=email,
            subject=f"Undangan bergabung {company_name} - Swarna PROPER Tracker",
            html=mailer.invitation_html(company_name, ROLE_LABELS.get(role, role), token),
        )
        await db.notification_log.insert_one({
            "id": new_id(), "company_id": None, "type": "invitation", "recipient_email": email,
            "channel": "email", "status": "terkirim", "sent_at": now_iso(),
            "message": f"Undangan {ROLE_LABELS.get(role, role)}",
        })
    except Exception as e:
        logger.error(f"Invite email failed: {e}")
        await db.notification_log.insert_one({
            "id": new_id(), "company_id": None, "type": "invitation", "recipient_email": email,
            "channel": "email", "status": "gagal", "sent_at": now_iso(), "message": str(e),
        })


@api.get("/companies")
async def list_companies(user: dict = Depends(get_current_user)):
    ids = await get_accessible_company_ids(user)
    rows = await db.companies.find({"id": {"$in": ids}}, {"_id": 0}).to_list(1000)
    return rows


@api.get("/companies/{company_id}")
async def get_company(company_id: str, user: dict = Depends(get_current_user)):
    ids = await get_accessible_company_ids(user)
    if company_id not in ids:
        raise HTTPException(status_code=403, detail="Tidak punya akses")
    c = await db.companies.find_one({"id": company_id}, {"_id": 0})
    if not c:
        raise HTTPException(status_code=404, detail="Perusahaan tidak ditemukan")
    return c


# ----------------------------- invitations (team) -----------------------------
@api.post("/invitations")
async def create_invite(body: InviteCreate, bg: BackgroundTasks,
                        company_id: str = Depends(get_company_id),
                        user: dict = Depends(require_roles(COMPANY_ADMIN, SWARNA_ADMIN))):
    if body.role not in (COMPANY_ADMIN, HRGA, SUPERVISOR):
        raise HTTPException(status_code=400, detail="Peran tidak valid")
    email = body.email.lower().strip()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=409, detail="Email sudah terdaftar")
    company = await db.companies.find_one({"id": company_id}, {"_id": 0})
    token = new_id() + new_id().replace("-", "")
    inv = {
        "id": new_id(), "company_id": company_id, "email": email, "name": body.name or "",
        "role": body.role, "token": token, "used": False,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "created_at": now_iso(),
    }
    await db.invitations.insert_one(inv)
    bg.add_task(_send_invite_email, email, company["name"], body.role, token)
    return {"invite": clean(inv), "invite_link": f"{mailer.APP_BASE_URL}/invite/{token}"}


@api.get("/invitations")
async def list_invites(company_id: str = Depends(get_company_id), user: dict = Depends(get_current_user)):
    rows = await db.invitations.find({"company_id": company_id}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return rows


@api.get("/users")
async def list_users(company_id: str = Depends(get_company_id), user: dict = Depends(get_current_user)):
    rows = await db.users.find({"company_id": company_id}, {"_id": 0, "password_hash": 0}).to_list(1000)
    return rows


# ----------------------------- sites -----------------------------
@api.get("/sites")
async def list_sites(company_id: str = Depends(get_company_id), user: dict = Depends(get_current_user)):
    return await db.sites.find({"company_id": company_id}, {"_id": 0}).sort("created_at", 1).to_list(1000)


@api.post("/sites")
async def create_site(body: SiteBody, company_id: str = Depends(get_company_id),
                      user: dict = Depends(require_roles(COMPANY_ADMIN, HRGA, SWARNA_ADMIN))):
    site = {"id": new_id(), "company_id": company_id, "name": body.name,
            "address": body.address or "", "created_at": now_iso()}
    await db.sites.insert_one(site)
    return clean(site)


@api.put("/sites/{site_id}")
async def update_site(site_id: str, body: SiteBody, company_id: str = Depends(get_company_id),
                      user: dict = Depends(require_roles(COMPANY_ADMIN, HRGA, SWARNA_ADMIN))):
    r = await db.sites.update_one({"id": site_id, "company_id": company_id},
                                  {"$set": {"name": body.name, "address": body.address or ""}})
    if not r.matched_count:
        raise HTTPException(status_code=404, detail="Site tidak ditemukan")
    return await db.sites.find_one({"id": site_id}, {"_id": 0})


@api.delete("/sites/{site_id}")
async def delete_site(site_id: str, company_id: str = Depends(get_company_id),
                      user: dict = Depends(require_roles(COMPANY_ADMIN, SWARNA_ADMIN))):
    await db.monitoring_points.delete_many({"site_id": site_id, "company_id": company_id})
    await db.sites.delete_one({"id": site_id, "company_id": company_id})
    return {"ok": True}


# ----------------------------- monitoring points -----------------------------
def _serialize_params(params: List[ParameterBody]) -> list:
    out = []
    for p in params:
        out.append({"id": new_id(), "nama": p.nama, "satuan": p.satuan or "",
                    "baku_mutu": p.baku_mutu, "baku_mutu_min": p.baku_mutu_min})
    return out


@api.get("/monitoring-points")
async def list_points(site_id: Optional[str] = None, company_id: str = Depends(get_company_id),
                      user: dict = Depends(get_current_user)):
    q = {"company_id": company_id}
    if site_id:
        q["site_id"] = site_id
    rows = await db.monitoring_points.find(q, {"_id": 0}).to_list(1000)
    sites = {s["id"]: s["name"] for s in await db.sites.find({"company_id": company_id}, {"_id": 0}).to_list(1000)}
    today = date.today()
    for r in rows:
        r["site_name"] = sites.get(r["site_id"], "")
        due = r.get("tanggal_jatuh_tempo_berikutnya")
        r["days_until_due"] = (date.fromisoformat(due) - today).days if due else None
    return rows


@api.post("/monitoring-points")
async def create_point(body: MonitoringPointBody, company_id: str = Depends(get_company_id),
                       user: dict = Depends(require_roles(COMPANY_ADMIN, HRGA, SWARNA_ADMIN))):
    site = await db.sites.find_one({"id": body.site_id, "company_id": company_id})
    if not site:
        raise HTTPException(status_code=400, detail="Site tidak valid")
    point = {
        "id": new_id(), "company_id": company_id, "site_id": body.site_id, "name": body.name,
        "jenis": body.jenis, "frekuensi_bulan": body.frekuensi_bulan,
        "tanggal_uji_terakhir": body.tanggal_uji_terakhir,
        "tanggal_jatuh_tempo_berikutnya": compute_due(body.tanggal_uji_terakhir, body.frekuensi_bulan),
        "parameters": _serialize_params(body.parameters),
        "created_at": now_iso(),
    }
    await db.monitoring_points.insert_one(point)
    return clean(point)


@api.get("/monitoring-points/{point_id}")
async def get_point(point_id: str, company_id: str = Depends(get_company_id), user: dict = Depends(get_current_user)):
    p = await db.monitoring_points.find_one({"id": point_id, "company_id": company_id}, {"_id": 0})
    if not p:
        raise HTTPException(status_code=404, detail="Titik penaatan tidak ditemukan")
    site = await db.sites.find_one({"id": p["site_id"]}, {"_id": 0})
    p["site_name"] = site["name"] if site else ""
    due = p.get("tanggal_jatuh_tempo_berikutnya")
    p["days_until_due"] = (date.fromisoformat(due) - date.today()).days if due else None
    return p


@api.put("/monitoring-points/{point_id}")
async def update_point(point_id: str, body: MonitoringPointBody, company_id: str = Depends(get_company_id),
                       user: dict = Depends(require_roles(COMPANY_ADMIN, HRGA, SWARNA_ADMIN))):
    existing = await db.monitoring_points.find_one({"id": point_id, "company_id": company_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Titik penaatan tidak ditemukan")
    site = await db.sites.find_one({"id": body.site_id, "company_id": company_id})
    if not site:
        raise HTTPException(status_code=400, detail="Site tidak valid")
    # keep existing parameter ids when names match, else regenerate
    params = _serialize_params(body.parameters)
    upd = {
        "site_id": body.site_id, "name": body.name, "jenis": body.jenis,
        "frekuensi_bulan": body.frekuensi_bulan, "tanggal_uji_terakhir": body.tanggal_uji_terakhir,
        "tanggal_jatuh_tempo_berikutnya": compute_due(body.tanggal_uji_terakhir, body.frekuensi_bulan),
        "parameters": params,
    }
    await db.monitoring_points.update_one({"id": point_id}, {"$set": upd})
    return await db.monitoring_points.find_one({"id": point_id}, {"_id": 0})


@api.delete("/monitoring-points/{point_id}")
async def delete_point(point_id: str, company_id: str = Depends(get_company_id),
                       user: dict = Depends(require_roles(COMPANY_ADMIN, SWARNA_ADMIN))):
    await db.monitoring_points.delete_one({"id": point_id, "company_id": company_id})
    return {"ok": True}


# ----------------------------- labs -----------------------------
@api.get("/labs")
async def list_labs(company_id: str = Depends(get_company_id), user: dict = Depends(get_current_user)):
    labs = await db.labs.find({"company_id": company_id}, {"_id": 0}).to_list(1000)
    for lab in labs:
        rep = await db.lhu.find_one({"company_id": company_id, "lab_id": lab["id"], "is_deleted": False},
                                    {"_id": 0}, sort=[("tanggal_uji", -1)])
        lab["last_used"] = rep["tanggal_uji"] if rep else None
    return labs


@api.post("/labs")
async def create_lab(body: LabBody, company_id: str = Depends(get_company_id),
                     user: dict = Depends(require_roles(COMPANY_ADMIN, HRGA, SWARNA_ADMIN))):
    lab = {"id": new_id(), "company_id": company_id, **body.model_dump(), "created_at": now_iso()}
    await db.labs.insert_one(lab)
    return clean(lab)


@api.put("/labs/{lab_id}")
async def update_lab(lab_id: str, body: LabBody, company_id: str = Depends(get_company_id),
                     user: dict = Depends(require_roles(COMPANY_ADMIN, HRGA, SWARNA_ADMIN))):
    r = await db.labs.update_one({"id": lab_id, "company_id": company_id}, {"$set": body.model_dump()})
    if not r.matched_count:
        raise HTTPException(status_code=404, detail="Lab tidak ditemukan")
    return await db.labs.find_one({"id": lab_id}, {"_id": 0})


@api.delete("/labs/{lab_id}")
async def delete_lab(lab_id: str, company_id: str = Depends(get_company_id),
                     user: dict = Depends(require_roles(COMPANY_ADMIN, SWARNA_ADMIN))):
    await db.labs.delete_one({"id": lab_id, "company_id": company_id})
    return {"ok": True}


# ----------------------------- LHU / test reports -----------------------------
def _evaluate_results(results: list) -> list:
    out = []
    for r in results:
        nilai = r.get("nilai")
        bm = r.get("baku_mutu")
        bmin = r.get("baku_mutu_min")
        status = "sesuai"
        try:
            v = float(nilai)
            if bm is not None and v > float(bm):
                status = "melebihi"
            if bmin is not None and v < float(bmin):
                status = "melebihi"
        except (TypeError, ValueError):
            status = "sesuai"
        out.append({**r, "status": status})
    return out


@api.post("/monitoring-points/{point_id}/lhu")
async def upload_lhu(point_id: str, file: UploadFile = File(...), periode: str = Form(...),
                     tanggal_uji: str = Form(...), lab_id: str = Form(""), results: str = Form("[]"),
                     company_id: str = Depends(get_company_id),
                     user: dict = Depends(require_roles(COMPANY_ADMIN, HRGA, SUPERVISOR, SWARNA_ADMIN))):
    point = await db.monitoring_points.find_one({"id": point_id, "company_id": company_id})
    if not point:
        raise HTTPException(status_code=404, detail="Titik penaatan tidak ditemukan")
    if lab_id:
        lab = await db.labs.find_one({"id": lab_id, "company_id": company_id})
        if not lab:
            raise HTTPException(status_code=400, detail="Lab tidak valid untuk perusahaan ini")
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "bin"
    path = f"{storage.APP_NAME}/{company_id}/lhu/{new_id()}.{ext}"
    data = await file.read()
    content_type = storage.MIME_TYPES.get(ext, file.content_type or "application/octet-stream")
    result = await asyncio.to_thread(storage.put_object, path, data, content_type)
    # Evaluate strictly against stored monitoring-point parameters (ignore client-supplied limits)
    try:
        client_results = json.loads(results)
    except Exception:
        client_results = []
    client_map = {str(r.get("nama")): r.get("nilai") for r in client_results if isinstance(r, dict)}
    merged = []
    for meta in point.get("parameters", []):
        merged.append({
            "nama": meta["nama"], "satuan": meta.get("satuan", ""),
            "baku_mutu": meta.get("baku_mutu"), "baku_mutu_min": meta.get("baku_mutu_min"),
            "nilai": client_map.get(meta["nama"]),
        })
    parsed = _evaluate_results(merged)
    report = {
        "id": new_id(), "company_id": company_id, "monitoring_point_id": point_id,
        "periode": periode, "tanggal_uji": tanggal_uji, "lab_id": lab_id or None,
        "storage_path": result["path"], "original_filename": file.filename,
        "content_type": content_type, "size": result.get("size", len(data)),
        "results": parsed, "is_deleted": False,
        "uploaded_by": user["id"], "created_at": now_iso(),
    }
    await db.lhu.insert_one(report)
    # recompute due date from latest test
    latest = await db.lhu.find({"monitoring_point_id": point_id, "is_deleted": False}, {"_id": 0, "tanggal_uji": 1}) \
        .sort("tanggal_uji", -1).to_list(1)
    last_test = latest[0]["tanggal_uji"] if latest else tanggal_uji
    await db.monitoring_points.update_one({"id": point_id}, {"$set": {
        "tanggal_uji_terakhir": last_test,
        "tanggal_jatuh_tempo_berikutnya": compute_due(last_test, point["frekuensi_bulan"]),
    }})
    return clean(report)


@api.get("/monitoring-points/{point_id}/lhu")
async def list_lhu(point_id: str, company_id: str = Depends(get_company_id), user: dict = Depends(get_current_user)):
    rows = await db.lhu.find({"monitoring_point_id": point_id, "company_id": company_id, "is_deleted": False},
                             {"_id": 0}).sort("tanggal_uji", -1).to_list(1000)
    labs = {l["id"]: l["nama"] for l in await db.labs.find({"company_id": company_id}, {"_id": 0}).to_list(1000)}
    for r in rows:
        r["lab_name"] = labs.get(r.get("lab_id"), "")
    return rows


@api.delete("/lhu/{report_id}")
async def delete_lhu(report_id: str, company_id: str = Depends(get_company_id),
                     user: dict = Depends(require_roles(COMPANY_ADMIN, HRGA, SWARNA_ADMIN))):
    await db.lhu.update_one({"id": report_id, "company_id": company_id}, {"$set": {"is_deleted": True}})
    return {"ok": True}


@api.get("/files/{path:path}")
async def download_file(path: str, user: dict = Depends(get_current_user)):
    record = await db.lhu.find_one({"storage_path": path, "is_deleted": False}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail="File tidak ditemukan")
    ids = await get_accessible_company_ids(user)
    if record["company_id"] not in ids:
        raise HTTPException(status_code=403, detail="Tidak punya akses")
    data, content_type = await asyncio.to_thread(storage.get_object, path)
    return Response(content=data, media_type=record.get("content_type", content_type))


# ----------------------------- dashboard -----------------------------
@api.get("/dashboard")
async def dashboard(company_id: str = Depends(get_company_id), user: dict = Depends(get_current_user)):
    points = await db.monitoring_points.find({"company_id": company_id}, {"_id": 0}).to_list(1000)
    sites = {s["id"]: s["name"] for s in await db.sites.find({"company_id": company_id}, {"_id": 0}).to_list(1000)}
    today = date.today()
    overdue, due7, due14, due30, ok = [], [], [], [], []
    for p in points:
        due = p.get("tanggal_jatuh_tempo_berikutnya")
        item = {"id": p["id"], "name": p["name"], "jenis": p["jenis"],
                "site_name": sites.get(p["site_id"], ""), "due_date": due,
                "frekuensi_bulan": p["frekuensi_bulan"],
                "belum_pernah_uji": not p.get("tanggal_uji_terakhir")}
        if not due:
            item["days"] = None
            overdue.append(item) if item["belum_pernah_uji"] else ok.append(item)
            continue
        days = (date.fromisoformat(due) - today).days
        item["days"] = days
        if days < 0:
            overdue.append(item)
        elif days <= 7:
            due7.append(item)
        elif days <= 14:
            due14.append(item)
        elif days <= 30:
            due30.append(item)
        else:
            ok.append(item)
    overdue.sort(key=lambda x: (x["days"] is not None, x["days"] if x["days"] is not None else 0))
    return {
        "overdue": overdue, "due_7": due7, "due_14": due14, "due_30": due30,
        "total_points": len(points), "ok_count": len(ok),
        "compliance": await _compliance(company_id, points),
    }


async def _compliance(company_id: str, points: list) -> dict:
    today = date.today()
    total = len(points)
    taat = 0
    detail = []
    for p in points:
        due = p.get("tanggal_jatuh_tempo_berikutnya")
        on_time = bool(due) and date.fromisoformat(due) >= today
        latest = await db.lhu.find({"monitoring_point_id": p["id"], "is_deleted": False}, {"_id": 0}) \
            .sort("tanggal_uji", -1).to_list(1)
        hasil_sesuai = True
        if latest:
            hasil_sesuai = all(r.get("status") == "sesuai" for r in latest[0].get("results", []))
        else:
            on_time = False
        compliant = on_time and hasil_sesuai
        if compliant:
            taat += 1
        detail.append({"id": p["id"], "name": p["name"], "on_time": on_time,
                       "hasil_sesuai": hasil_sesuai, "compliant": compliant})
    pct = round((taat / total) * 100) if total else 0
    color = "green" if pct >= 90 else ("yellow" if pct >= 60 else "red")
    return {"percent": pct, "color": color, "taat": taat, "total": total, "detail": detail}


@api.get("/compliance")
async def compliance(company_id: str = Depends(get_company_id), user: dict = Depends(get_current_user)):
    points = await db.monitoring_points.find({"company_id": company_id}, {"_id": 0}).to_list(1000)
    return await _compliance(company_id, points)


# ----------------------------- trend -----------------------------
@api.get("/monitoring-points/{point_id}/trend")
async def trend(point_id: str, parameter: str, company_id: str = Depends(get_company_id),
                user: dict = Depends(get_current_user)):
    point = await db.monitoring_points.find_one({"id": point_id, "company_id": company_id}, {"_id": 0})
    if not point:
        raise HTTPException(status_code=404, detail="Titik penaatan tidak ditemukan")
    reports = await db.lhu.find({"monitoring_point_id": point_id, "company_id": company_id, "is_deleted": False},
                                {"_id": 0}).sort("tanggal_uji", 1).to_list(1000)
    param_meta = next((p for p in point.get("parameters", []) if p["nama"] == parameter), None)
    baku_mutu = param_meta.get("baku_mutu") if param_meta else None
    baku_mutu_min = param_meta.get("baku_mutu_min") if param_meta else None
    series = []
    for rep in reports:
        match = next((r for r in rep.get("results", []) if r.get("nama") == parameter), None)
        if match is None or match.get("nilai") in (None, ""):
            continue
        try:
            v = float(match["nilai"])
        except (TypeError, ValueError):
            continue
        series.append({"periode": rep["periode"], "tanggal": rep["tanggal_uji"], "nilai": v,
                       "status": match.get("status", "sesuai")})
    change_percent = None
    perlu_perhatian = False
    if len(series) >= 2:
        prev, last = series[-2]["nilai"], series[-1]["nilai"]
        if prev:
            change_percent = round(((last - prev) / abs(prev)) * 100, 1)
        if baku_mutu is not None and last >= 0.8 * float(baku_mutu):
            perlu_perhatian = True
        if len(series) >= 3 and series[-1]["nilai"] > series[-2]["nilai"] > series[-3]["nilai"] and baku_mutu is not None:
            perlu_perhatian = True
    return {
        "parameter": parameter, "satuan": param_meta.get("satuan", "") if param_meta else "",
        "baku_mutu": baku_mutu, "baku_mutu_min": baku_mutu_min,
        "series": series, "change_percent": change_percent, "perlu_perhatian": perlu_perhatian,
    }


# ----------------------------- notification log -----------------------------
@api.get("/notifications")
async def notifications(company_id: str = Depends(get_company_id), user: dict = Depends(get_current_user)):
    return await db.notification_log.find({"company_id": company_id}, {"_id": 0}) \
        .sort("sent_at", -1).to_list(500)


# ----------------------------- whatsapp settings (platform) -----------------------------
@api.get("/settings/whatsapp")
async def get_wa(user: dict = Depends(require_roles(SWARNA_ADMIN))):
    cfg = await db.settings.find_one({"id": "whatsapp"}, {"_id": 0})
    if not cfg:
        cfg = {"id": "whatsapp", "enabled": False, "api_url": "", "api_key": "", "sender_number": ""}
    cfg["configured"] = bool(cfg.get("enabled") and cfg.get("api_url") and cfg.get("api_key"))
    cfg["api_key"] = "****" if cfg.get("api_key") else ""
    return cfg


@api.put("/settings/whatsapp")
async def set_wa(body: WhatsAppConfigBody, user: dict = Depends(require_roles(SWARNA_ADMIN))):
    update = body.model_dump()
    if update.get("api_key") in ("", "****"):
        update.pop("api_key", None)
    await db.settings.update_one({"id": "whatsapp"}, {"$set": {"id": "whatsapp", **update}}, upsert=True)
    cfg = await db.settings.find_one({"id": "whatsapp"}, {"_id": 0})
    cfg["configured"] = bool(cfg.get("enabled") and cfg.get("api_url") and cfg.get("api_key"))
    cfg["api_key"] = "****" if cfg.get("api_key") else ""
    return cfg


# ----------------------------- reminder engine -----------------------------
async def _wa_config() -> Optional[dict]:
    cfg = await db.settings.find_one({"id": "whatsapp"}, {"_id": 0})
    if cfg and cfg.get("enabled") and cfg.get("api_url") and cfg.get("api_key"):
        return cfg
    return None


async def _send_whatsapp(cfg: dict, to: str, message: str):
    import httpx
    async with httpx.AsyncClient(timeout=20) as cx:
        resp = await cx.post(cfg["api_url"],
                             headers={"Authorization": f"Bearer {cfg['api_key']}"},
                             json={"from": cfg.get("sender_number"), "to": to, "message": message})
        resp.raise_for_status()


async def run_reminder_check():
    today = date.today()
    companies = await db.companies.find({}, {"_id": 0, "id": 1, "name": 1}).to_list(1000)
    wa_cfg = await _wa_config()
    sent = 0
    for comp in companies:
        cid = comp["id"]
        # recipients: company users + assigned swarna admins
        team = await db.users.find({"company_id": cid, "role": {"$in": [COMPANY_ADMIN, HRGA, SUPERVISOR]}},
                                   {"_id": 0, "email": 1, "name": 1, "phone": 1}).to_list(1000)
        assigns = await db.assignments.find({"company_id": cid}, {"_id": 0, "swarna_user_id": 1}).to_list(1000)
        swarna_ids = [a["swarna_user_id"] for a in assigns]
        swarna = await db.users.find({"id": {"$in": swarna_ids}}, {"_id": 0, "email": 1, "name": 1, "phone": 1}).to_list(1000)
        recipients = team + swarna
        if not recipients:
            continue
        sites = {s["id"]: s["name"] for s in await db.sites.find({"company_id": cid}, {"_id": 0}).to_list(1000)}
        points = await db.monitoring_points.find({"company_id": cid}, {"_id": 0}).to_list(1000)
        for p in points:
            due = p.get("tanggal_jatuh_tempo_berikutnya")
            if not due:
                continue
            days = (date.fromisoformat(due) - today).days
            threshold = None
            for t in REMINDER_THRESHOLDS:
                if days <= t:
                    threshold = t
            if threshold is None:
                continue
            key = f"{p['id']}|{due}|H-{threshold}"
            if await db.notification_log.find_one({"dedup_key": key}):
                continue
            site_name = sites.get(p["site_id"], "")
            jenis_label = "Air Limbah" if p["jenis"] == "air_limbah" else "Emisi Udara"
            html = mailer.reminder_html(comp["name"], site_name, p["name"], jenis_label, due, days)
            subject = f"[PROPER] Pengingat uji {p['name']} - {comp['name']}"
            for rcp in recipients:
                if rcp.get("email"):
                    status, err = "terkirim", None
                    try:
                        await mailer.send_email(to=rcp["email"], subject=subject, html=html)
                    except Exception as e:
                        status, err = "gagal", str(e)
                    await db.notification_log.insert_one({
                        "id": new_id(), "dedup_key": key, "company_id": cid, "type": f"H-{threshold}",
                        "monitoring_point_id": p["id"], "monitoring_point_name": p["name"],
                        "recipient_email": rcp["email"], "recipient_name": rcp.get("name", ""),
                        "channel": "email", "status": status, "sent_at": now_iso(),
                        "message": err or f"Reminder H-{threshold} ({days} hari)",
                    })
                    sent += 1
                if wa_cfg and rcp.get("phone"):
                    status, err = "terkirim", None
                    try:
                        await _send_whatsapp(wa_cfg, rcp["phone"],
                                             f"Pengingat PROPER: {p['name']} ({comp['name']}) jatuh tempo {due}.")
                    except Exception as e:
                        status, err = "gagal", str(e)
                    await db.notification_log.insert_one({
                        "id": new_id(), "dedup_key": key + "|wa|" + rcp["phone"], "company_id": cid,
                        "type": f"H-{threshold}", "monitoring_point_id": p["id"],
                        "monitoring_point_name": p["name"], "recipient_email": rcp.get("phone"),
                        "recipient_name": rcp.get("name", ""), "channel": "whatsapp",
                        "status": status, "sent_at": now_iso(), "message": err or "WA reminder",
                    })
    logger.info(f"Reminder check done. Emails attempted: {sent}")
    return sent


@api.post("/cron/reminders")
async def cron_reminders(request: Request, bg: BackgroundTasks, authorization: str = Header(None)):
    # Cron endpoints must ack 2xx immediately; enqueue/background the actual work.
    secret = os.environ.get("WEBHOOK_CRON_SECRET", "")
    token = authorization[7:] if authorization and authorization.startswith("Bearer ") else ""
    if not secret or not hmac.compare_digest(token, secret):
        raise HTTPException(status_code=401, detail="Unauthorized")
    bg.add_task(run_reminder_check)
    return {"accepted": True}


@api.post("/reminders/run-now")
async def run_now(user: dict = Depends(require_roles(SWARNA_ADMIN))):
    count = await run_reminder_check()
    return {"ok": True, "emails_attempted": count}


@api.get("/")
async def root():
    return {"message": "Swarna PROPER Tracker API"}


# ----------------------------- startup -----------------------------
async def seed_admin():
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@example.com").lower()
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        await db.users.insert_one({
            "id": new_id(), "email": admin_email, "password_hash": hash_password(admin_password),
            "name": "Admin Swarna", "role": SWARNA_ADMIN, "company_id": None,
            "phone": "", "email_verified": True, "created_at": now_iso(),
        })
        logger.info("Seeded Swarna admin")
    elif not verify_password(admin_password, existing.get("password_hash", "")):
        await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_password(admin_password)}})


@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await db.invitations.create_index("token", unique=True)
    await db.notification_log.create_index("dedup_key")
    await db.login_attempts.create_index("identifier")
    await seed_admin()
    try:
        storage.init_storage()
        logger.info("Storage initialized")
    except Exception as e:
        logger.error(f"Storage init failed: {e}")


@app.on_event("shutdown")
async def shutdown():
    client.close()


app.include_router(api)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=False,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
