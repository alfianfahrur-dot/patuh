import os
import re
import ipaddress
import logging
import httpx
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

EMAIL_BASE_URL = "https://integrations.emergentagent.com"
EMAIL_KEY = os.environ.get("EMERGENT_EMAIL_KEY")
EMAIL_FROM_NAME = os.environ.get("EMAIL_FROM_NAME", "PATUH")
EMAIL_REPLY_TO = os.environ.get("EMAIL_REPLY_TO")
APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:3000")

_SHORTENERS = ("bit.ly", "tinyurl.com", "t.co", "is.gd", "cutt.ly", "goo.gl", "rebrand.ly")
_CRED_ASK = ("reply with your password", "reply with the code", "send your password", "cvv",
             "send us your password", "enter your password below", "confirm your card number",
             "your full card number", "seed phrase", "recovery phrase", "verify your card",
             "social security number", "confirm your bank details")
_HOSTISH = re.compile(r"\b(?:https?://)?((?:[a-z0-9-]+\.)+[a-z]{2,})", re.I)


def _host_ok(host: str) -> bool:
    if not host or "xn--" in host:
        return False
    try:
        ipaddress.ip_address(host)
        return False
    except ValueError:
        pass
    return not any(host == s or host.endswith("." + s) for s in _SHORTENERS)


def _same_site(shown: str, real: str) -> bool:
    return shown == real or real.endswith("." + shown) or shown.endswith("." + real)


class _EmailScan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags, self.urls, self.anchors = set(), [], []
        self._href, self._text = None, []

    def handle_starttag(self, tag, attrs):
        self.tags.add(tag.lower())
        self.urls += [v for k, v in attrs if k.lower() in ("href", "src") and v]
        if tag.lower() == "a":
            self._href = dict((k.lower(), v) for k, v in attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._href is not None:
            self.anchors.append((self._href, "".join(self._text)))
            self._href, self._text = None, []


def _assert_safe_email(subject: str, html: str) -> None:
    scan = _EmailScan()
    scan.feed(html)
    if scan.tags & {"form", "input", "textarea", "select"}:
        raise ValueError("No forms or input fields in email (G2)")
    body = f"{subject}\n{html}".lower()
    for p in _CRED_ASK:
        if p in body:
            raise ValueError(f"Email asks the recipient for credentials: {p!r} (G2)")
    for url in scan.urls:
        low = url.strip().lower()
        if low.startswith(("mailto:", "tel:", "cid:", "#")):
            continue
        if not low.startswith("https://"):
            raise ValueError(f"Email links/assets must be absolute https: {url!r} (G3)")
        host = urlparse(low).hostname or ""
        if not _host_ok(host) or urlparse(low).username is not None:
            raise ValueError(f"Shortened, numeric-host or credential-bearing URL: {url!r} (G3)")
    for href, text in scan.anchors:
        real = urlparse(href.strip().lower()).hostname or ""
        if not real:
            continue
        for m in _HOSTISH.finditer(text):
            if not _same_site(m.group(1).lower(), real):
                raise ValueError(f"Anchor text {m.group(1)!r} != real link host {real!r} (G3)")


async def send_email(*, to: str, subject: str, html: str) -> str | None:
    _assert_safe_email(subject, html)
    payload = {"to": [to], "subject": subject, "html": html, "from_name": EMAIL_FROM_NAME}
    if EMAIL_REPLY_TO:
        payload["contact_email"] = EMAIL_REPLY_TO
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{EMAIL_BASE_URL}/api/v1/email/send",
            headers={"X-Email-Key": EMAIL_KEY},
            json=payload,
        )
    resp.raise_for_status()
    return resp.json().get("id")


def _shell(inner: str) -> str:
    return (
        '<table role="presentation" width="100%" style="background:#F8FAFC;padding:24px 0">'
        '<tr><td align="center">'
        '<table role="presentation" width="600" style="background:#FFFFFF;border-radius:12px;'
        'overflow:hidden;font-family:Arial,sans-serif;border:1px solid #E2E8F0">'
        '<tr><td style="background:#064E3B;padding:20px 28px">'
        '<span style="color:#FFFFFF;font-size:18px;font-weight:bold">PATUH</span>'
        '<span style="color:#A7F3D0;font-size:12px;margin-left:8px">Tepat Waktu, Tetap Taat</span>'
        '</td></tr>'
        f'<tr><td style="padding:28px">{inner}'
        '<p style="font-size:12px;color:#94A3B8;margin-top:28px">Dikirim oleh PATUH. '
        'Kami tidak pernah meminta kata sandi Anda melalui email.</p>'
        '</td></tr></table></td></tr></table>'
    )


def invitation_html(company_name: str, role_label: str, token: str) -> str:
    link = f"{APP_BASE_URL}/invite/{escape(token)}"
    inner = (
        f'<h2 style="color:#064E3B;margin:0 0 12px">Anda diundang bergabung</h2>'
        f'<p style="color:#334155;font-size:15px">Anda diundang sebagai <strong>{escape(role_label)}</strong> '
        f'untuk perusahaan <strong>{escape(company_name)}</strong> di PATUH.</p>'
        f'<p style="color:#334155;font-size:15px">Klik tombol di bawah untuk membuat kata sandi dan mengaktifkan akun Anda.</p>'
        f'<p style="margin:24px 0"><a href="{link}" style="background:#059669;color:#FFFFFF;'
        f'text-decoration:none;padding:12px 26px;border-radius:8px;font-weight:bold;font-size:15px">'
        f'Buat Kata Sandi</a></p>'
        f'<p style="color:#94A3B8;font-size:13px">Tautan ini berlaku 7 hari dan hanya bisa dipakai sekali.</p>'
    )
    return _shell(inner)


def verification_html(name: str, token: str) -> str:
    link = f"{APP_BASE_URL}/verify-email/{escape(token)}"
    inner = (
        f'<h2 style="color:#064E3B;margin:0 0 12px">Verifikasi email Anda</h2>'
        f'<p style="color:#334155;font-size:15px">Halo {escape(name) or "Admin"}, terima kasih telah mendaftarkan '
        f'perusahaan Anda di PATUH.</p>'
        f'<p style="color:#334155;font-size:15px">Klik tombol di bawah untuk memverifikasi email dan mengaktifkan akun Anda.</p>'
        f'<p style="margin:24px 0"><a href="{link}" style="background:#059669;color:#FFFFFF;'
        f'text-decoration:none;padding:12px 26px;border-radius:8px;font-weight:bold;font-size:15px">'
        f'Verifikasi Email</a></p>'
        f'<p style="color:#94A3B8;font-size:13px">Tautan ini berlaku 2 hari. Jika Anda tidak mendaftar, abaikan email ini.</p>'
    )
    return _shell(inner)


def reset_html(name: str, token: str) -> str:
    link = f"{APP_BASE_URL}/reset-password/{escape(token)}"
    inner = (
        f'<h2 style="color:#064E3B;margin:0 0 12px">Reset kata sandi</h2>'
        f'<p style="color:#334155;font-size:15px">Halo {escape(name) or "rekan"}, kami menerima permintaan untuk '
        f'mengatur ulang kata sandi akun PATUH Anda.</p>'
        f'<p style="color:#334155;font-size:15px">Klik tombol di bawah untuk membuat kata sandi baru.</p>'
        f'<p style="margin:24px 0"><a href="{link}" style="background:#059669;color:#FFFFFF;'
        f'text-decoration:none;padding:12px 26px;border-radius:8px;font-weight:bold;font-size:15px">'
        f'Reset Kata Sandi</a></p>'
        f'<p style="color:#94A3B8;font-size:13px">Tautan ini berlaku 1 jam dan hanya bisa dipakai sekali. '
        f'Jika Anda tidak meminta reset, abaikan email ini.</p>'
    )
    return _shell(inner)


def reminder_html(company_name: str, site_name: str, point_name: str, jenis: str,
                  due_date: str, days: int) -> str:
    if days < 0:
        status = f'<span style="color:#991B1B;font-weight:bold">SUDAH TELAT {abs(days)} hari</span>'
        tone = "#FEF2F2"
    elif days == 0:
        status = '<span style="color:#991B1B;font-weight:bold">JATUH TEMPO HARI INI</span>'
        tone = "#FEF2F2"
    else:
        status = f'<span style="color:#92400E;font-weight:bold">Jatuh tempo dalam {days} hari</span>'
        tone = "#FFFBEB"
    inner = (
        f'<h2 style="color:#064E3B;margin:0 0 12px">Pengingat Jadwal Pengujian</h2>'
        f'<div style="background:{tone};border-radius:8px;padding:16px;margin:12px 0">'
        f'<p style="margin:0 0 6px;font-size:16px">{status}</p>'
        f'<p style="margin:0;color:#334155;font-size:15px"><strong>{escape(point_name)}</strong> '
        f'({escape(jenis)}) &mdash; {escape(site_name)}</p>'
        f'<p style="margin:6px 0 0;color:#334155;font-size:14px">Perusahaan: {escape(company_name)}</p>'
        f'<p style="margin:6px 0 0;color:#334155;font-size:14px">Tanggal jatuh tempo: {escape(due_date)}</p>'
        f'</div>'
        f'<p style="color:#334155;font-size:15px">Segera jadwalkan pengambilan sampel ke laboratorium '
        f'agar pengujian tidak terlambat, lalu unggah Laporan Hasil Uji (LHU) di aplikasi.</p>'
        f'<p style="margin:20px 0"><a href="{APP_BASE_URL}" style="background:#059669;color:#FFFFFF;'
        f'text-decoration:none;padding:12px 24px;border-radius:8px;font-weight:bold">Buka Aplikasi</a></p>'
    )
    return _shell(inner)
