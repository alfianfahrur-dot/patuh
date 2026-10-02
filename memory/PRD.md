# Swarna PROPER Tracker — PRD

## Problem Statement
SaaS asisten kepatuhan PROPER (lingkungan, level Merah & Biru) untuk staf HRGA non-teknis.
Fokus: pengujian air limbah & emisi berkala TIDAK PERNAH telat, dan dokumen LHU TIDAK PERNAH tercecer.
Model akses invite-only dengan arsitektur siap self-signup (field status_pendaftaran & metode_masuk fleksibel).

## Architecture
- Backend: FastAPI (modular: server.py, auth_utils.py, email_service.py, storage_service.py, db.py). MongoDB (uuid string ids).
- Frontend: React + Tailwind + shadcn/ui + Recharts. Bearer token auth (localStorage), company_id as query param.
- Integrations: JWT custom auth; Resend (Emergent-managed email); Emergent object storage (LHU files); WhatsApp modular/disabled.
- Reminders: Emergent cron (.emergent/crons.yml) daily 08:00 WIB -> POST /api/cron/reminders (Bearer WEBHOOK_CRON_SECRET).

## Roles
- swarna_admin (platform): create/invite companies, assigned to companies via assignments, receives reminders.
- company_admin (client): manage sites/points, invite team.
- hrga: daily user — reminders, upload LHU, lab directory.
- supervisor: optional validation.

## Security (RLS)
- Every company-scoped query filtered by company_id via get_company_id dependency.
- Swarna admin limited to assigned companies (assignments collection).
- Invitation tokens single-use + 7-day expiry.
- Brute-force lockout: 5 fails -> 15 min lockout (login_attempts).
- Foreign site_id/lab_id rejected on point update & LHU upload.
- LHU results evaluated against STORED point parameters (client limits ignored).

## Data Model (collections)
companies, users (CompanyUsers), assignments (SwarnaConsultantAssignments), sites,
monitoring_points (embedded parameters[], tanggal_uji_terakhir, tanggal_jatuh_tempo_berikutnya computed),
lhu (TestReports: file ref + results[]), labs, notification_log, invitations, settings (whatsapp).

## Implemented (2026-10-01)
- Invite-only auth: login, accept-invite, validate-invite, me, logout, brute-force lockout.
- Admin Swarna panel: create company + auto-invite admin + auto-assign; WhatsApp config (masked key); run reminders now.
- Team invitations (company_admin invites hrga/supervisor/company_admin).
- Sites + Monitoring Points CRUD with embedded parameters & baku mutu; auto due-date computation (add_months).
- Dashboard: overdue (red, top) + due 7/14/30 + compliance score card + summary.
- Vault LHU: multipart upload (object storage) + per-parameter results vs baku mutu + chronological history + soft delete + file download.
- Lab directory with KAN badge + WhatsApp/call quick-contact (pre-filled message).
- Compliance score (green/yellow/red) + parameter trend (Recharts line + baku mutu ReferenceLine + % change badge + "Perlu Perhatian").
- Notification log (email/wa, terkirim/gagal).
- Reminder engine H-30/H-14/H-7/H via email to client team + assigned swarna admins; dedup via dedup_key; WA sent only if configured.
- Seeded demo company "PT Hijau Lestari" (admin budi.hrga@hijaulestari.co.id / Budi#2026) with sites, 3 points, 2 labs, 2 LHUs.

## Backlog
- P1: WhatsApp gateway live integration (provider-specific) once API key provided.
- P1: Supervisor approval step (optional single-level) before LHU final.
- P2: Self-signup public registration (schema already supports metode_masuk).
- P2: Report generator (SIMPEL), B3 tracking, Hijau/Emas modules (Phase 2 — out of MVP scope).

## Known / Notes
- WhatsApp reminders are MODULAR & DISABLED by default (email-only) until admin configures gateway.
- Email delivery via Resend works; transient 429 can occur under heavy concurrent sends.

## Feature: Saran Baku Mutu (2026-10-02)
- Data: backend/baku_mutu_seed.json (6 regulasi, 108 standar: 95 air_limbah, 12 emisi, 1 udara_ambien). Numbers kept verbatim.
- Collections: regulasi, baku_mutu_standar (fields aktif, diverifikasi_oleh/pada, versi, riwayat_perubahan), baku_mutu_audit.
- Backend (backend/baku_mutu.py pure logic + server.py endpoints):
  POST /api/admin/baku-mutu/seed (idempotent upsert, preserves verification on re-seed);
  GET /api/baku-mutu/standar?kategori=&q=; GET /api/baku-mutu/saran?kategori=&q=&debit=&bahan_bakar=&kapasitas_kw=
  (ranked + alasan_cocok + regulasi status + perlu_verifikasi + perlu_pilih_varian; debit variant selection for
  domestik >50/3-50/<=3 and tekstil <100/100-1000/>1000; fuel/capacity soft match for genset/boiler);
  POST /api/titik/{id}/terapkan-baku-mutu (snapshot params into point + standar_id + sumber_baku_mutu);
  admin mgmt: list/edit/verifikasi/regulasi/audit.
- Point parameter extended (additive): kode, tipe(maks|rentang|negatif), teks, periode, override, alasan;
  point: standar_id, snapshot_standar, sumber_baku_mutu(saran_otomatis|manual|persetujuan_teknis), sumber_catatan, kategori.
- Evaluation upgrade: statuses sesuai|mendekati(>=ambang*batas, default 80%, per-company ambang_peringatan_persen)|melebihi,
  + rentang(pH), negatif(Negatif), LOQ/"tidak terdeteksi"->sesuai, unit-mismatch guard. _compliance fails only on melebihi.
- Frontend: Sites point dialog has BakuMutuSuggest panel (search by kegiatan + debit/fuel/kW, cards with regulasi badge,
  perlu_verifikasi banner, revoked warning, param table, Terapkan) + baku-mutu-khusus override w/ wajib sumber + disclaimer.
  Admin has "Baku Mutu" tab (seed, list, filter perlu-verifikasi, verifikasi, audit).
- Tests: backend/tests/test_baku_mutu.py (12 pass), backend/validate_seed.py (pass, no dup ids, refs valid).
- MANUAL VERIFICATION PENDING: 32 standar flagged perlu_verifikasi=true (esp. domestik 11/2025 merged-cell extraction,
  tekstil 12/2025 secondary-source numbers) — must be checked against official PDFs before use for reporting.
- Out of scope (design-ready via seed/admin): most beban-pencemaran sectors, mining/migas/PLTU/semen emisi, baku mutu daerah.
