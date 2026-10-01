import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "@/lib/api";
import { JENIS_LABEL, dueLabel, formatDate } from "@/lib/helpers";
import { AlertTriangle, Clock, CheckCircle2, ArrowRight, ShieldCheck, Droplets, Factory, CalendarClock } from "lucide-react";

const COLOR = {
  green: { bg: "#ECFDF5", text: "#065F46", ring: "#10B981" },
  yellow: { bg: "#FFFBEB", text: "#92400E", ring: "#F59E0B" },
  red: { bg: "#FEF2F2", text: "#991B1B", ring: "#DC2626" },
};

function JenisIcon({ jenis, className }) {
  return jenis === "air_limbah" ? <Droplets className={className} /> : <Factory className={className} />;
}

function PointRow({ p, tone }) {
  return (
    <Link to="/vault" className="flex items-center justify-between gap-3 px-4 py-3 rounded-xl border bg-white hover:shadow-sm transition-all group"
      style={{ borderColor: tone.border }} data-testid={`due-point-${p.id}`}>
      <div className="flex items-center gap-3 min-w-0">
        <div className="h-9 w-9 rounded-lg grid place-items-center shrink-0" style={{ background: tone.bg }}>
          <JenisIcon jenis={p.jenis} className="h-[18px] w-[18px]" />
        </div>
        <div className="min-w-0">
          <div className="font-semibold text-emerald-950 truncate">{p.name}</div>
          <div className="text-xs text-slate-500 truncate">{JENIS_LABEL[p.jenis]} · {p.site_name}</div>
        </div>
      </div>
      <div className="text-right shrink-0">
        <div className="text-sm font-bold" style={{ color: tone.text }}>
          {p.belum_pernah_uji ? "Belum pernah diuji" : dueLabel(p.days)}
        </div>
        <div className="text-[11px] text-slate-400">{formatDate(p.due_date)}</div>
      </div>
      <ArrowRight className="h-4 w-4 text-slate-300 group-hover:text-emerald-600 shrink-0" />
    </Link>
  );
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.get("/dashboard").then(({ data }) => setData(data)).catch((e) => setErr(e?.response?.data?.detail || "Gagal memuat"));
  }, []);

  if (err) return <div className="text-slate-500">{typeof err === "string" ? err : "Belum ada perusahaan."}</div>;
  if (!data) return <div className="text-slate-400 animate-pulse">Memuat dashboard…</div>;

  const c = COLOR[data.compliance.color];
  const overdue = data.overdue || [];
  const soon = [...(data.due_7 || []), ...(data.due_14 || [])];
  const later = data.due_30 || [];

  return (
    <div className="animate-fade-up space-y-6">
      <div>
        <h1 className="font-head text-3xl font-bold text-emerald-950">Apa yang harus saya lakukan sekarang?</h1>
        <p className="text-slate-500 mt-1">Pantau jadwal pengujian air limbah & emisi. Yang telat tampil paling atas.</p>
      </div>

      {overdue.length > 0 ? (
        <div className="rounded-2xl border-2 border-[#DC2626] bg-[#FEF2F2] p-5" data-testid="overdue-banner">
          <div className="flex items-center gap-2 text-[#991B1B]">
            <AlertTriangle className="h-6 w-6" />
            <span className="font-head font-bold text-lg">
              {overdue.length} Titik Pengujian Perlu Tindakan Segera
            </span>
          </div>
          <p className="text-sm text-[#991B1B]/80 mt-1 mb-4">
            Titik berikut sudah telat atau belum pernah diuji. Segera hubungi lab & jadwalkan pengambilan sampel.
          </p>
          <div className="grid gap-2">
            {overdue.map((p) => <PointRow key={p.id} p={p} tone={{ bg: "#FEE2E2", text: "#991B1B", border: "#FCA5A5" }} />)}
          </div>
        </div>
      ) : (
        <div className="rounded-2xl border-2 border-[#A7F3D0] bg-[#ECFDF5] p-5 flex items-center gap-3" data-testid="all-clear-banner">
          <CheckCircle2 className="h-7 w-7 text-emerald-600" />
          <div>
            <div className="font-head font-bold text-lg text-emerald-800">Tidak ada yang telat. Kerja bagus!</div>
            <div className="text-sm text-emerald-700/80">Semua titik penaatan terjadwal dengan baik.</div>
          </div>
        </div>
      )}

      <div className="grid lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 space-y-5">
          <section className="bg-white rounded-2xl border border-slate-200 p-5" data-testid="due-soon-section">
            <div className="flex items-center gap-2 mb-4">
              <Clock className="h-5 w-5 text-amber-500" />
              <h2 className="font-head text-lg font-semibold text-emerald-950">Segera Jatuh Tempo (≤ 14 hari)</h2>
            </div>
            {soon.length ? (
              <div className="grid gap-2">{soon.map((p) => <PointRow key={p.id} p={p} tone={{ bg: "#FEF3C7", text: "#92400E", border: "#FDE68A" }} />)}</div>
            ) : <p className="text-sm text-slate-400 py-4">Tidak ada titik yang jatuh tempo dalam 14 hari.</p>}
          </section>

          <section className="bg-white rounded-2xl border border-slate-200 p-5" data-testid="due-30-section">
            <div className="flex items-center gap-2 mb-4">
              <CalendarClock className="h-5 w-5 text-emerald-500" />
              <h2 className="font-head text-lg font-semibold text-emerald-950">Rencana Berikutnya (15–30 hari)</h2>
            </div>
            {later.length ? (
              <div className="grid gap-2">{later.map((p) => <PointRow key={p.id} p={p} tone={{ bg: "#ECFDF5", text: "#065F46", border: "#A7F3D0" }} />)}</div>
            ) : <p className="text-sm text-slate-400 py-4">Belum ada jadwal dalam rentang ini.</p>}
          </section>
        </div>

        <div className="space-y-5">
          <section className="bg-white rounded-2xl border border-slate-200 p-5" data-testid="compliance-card">
            <div className="flex items-center gap-2 mb-4">
              <ShieldCheck className="h-5 w-5 text-emerald-600" />
              <h2 className="font-head text-lg font-semibold text-emerald-950">Skor Ketaatan</h2>
            </div>
            <div className="rounded-2xl p-6 text-center" style={{ background: c.bg }}>
              <div className="text-5xl font-head font-bold" style={{ color: c.text }}>{data.compliance.percent}%</div>
              <div className="text-sm mt-1" style={{ color: c.text }}>
                {data.compliance.taat} dari {data.compliance.total} titik taat
              </div>
            </div>
            <div className="mt-4 h-2.5 rounded-full bg-slate-100 overflow-hidden">
              <div className="h-full rounded-full transition-all" style={{ width: `${data.compliance.percent}%`, background: c.ring }} />
            </div>
            <p className="text-xs text-slate-500 mt-3">
              Taat = diuji tepat waktu <span className="font-semibold">dan</span> hasil sesuai baku mutu.
            </p>
          </section>

          <section className="bg-white rounded-2xl border border-slate-200 p-5" data-testid="summary-card">
            <h2 className="font-head text-lg font-semibold text-emerald-950 mb-3">Ringkasan</h2>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: "Total Titik", value: data.total_points, color: "#064E3B" },
                { label: "Terjadwal Aman", value: data.ok_count, color: "#059669" },
                { label: "Telat / Belum Uji", value: overdue.length, color: "#DC2626" },
                { label: "≤ 30 hari", value: soon.length + later.length, color: "#F59E0B" },
              ].map((s) => (
                <div key={s.label} className="rounded-xl bg-slate-50 p-3">
                  <div className="text-2xl font-head font-bold" style={{ color: s.color }}>{s.value}</div>
                  <div className="text-xs text-slate-500">{s.label}</div>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
