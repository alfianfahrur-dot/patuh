import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import {
  MapPin, Droplets, FlaskConical, Upload, Users, CheckCircle2, Circle, ArrowRight, Sparkles, PartyPopper,
} from "lucide-react";

export default function Onboarding({ onReady }) {
  const { user } = useAuth();
  const [st, setSt] = useState(null);

  useEffect(() => {
    Promise.all([api.get("/sites"), api.get("/monitoring-points"), api.get("/labs")])
      .then(([s, p, l]) => {
        setSt({
          sites: s.data.length,
          points: p.data.length,
          labs: l.data.length,
          tested: p.data.some((x) => x.tanggal_uji_terakhir),
        });
      })
      .catch(() => setSt({ sites: 0, points: 0, labs: 0, tested: false }));
  }, []);

  if (!st) return <div className="text-slate-400 animate-pulse">Menyiapkan panduan…</div>;

  const canInvite = user.role === "company_admin" || user.role === "swarna_admin";

  const steps = [
    {
      key: "site", icon: MapPin, to: "/sites", cta: "Buat Site",
      title: "Buat Site (lokasi) pertama Anda",
      desc: "Mis. 'Pabrik Cikarang'. Satu perusahaan bisa punya banyak site.",
      done: st.sites > 0,
    },
    {
      key: "point", icon: Droplets, to: "/sites", cta: "Tambah Titik Uji",
      title: "Tambah Titik Penaatan + parameter",
      desc: "Mis. Outlet IPAL / Cerobong. Isi parameter wajib uji, baku mutu, dan frekuensinya.",
      done: st.points > 0,
    },
    {
      key: "lab", icon: FlaskConical, to: "/lab", cta: "Tambah Lab", optional: true,
      title: "Simpan kontak Laboratorium",
      desc: "Agar bisa 'Hubungi Lab' satu klik saat titik mendekati jatuh tempo.",
      done: st.labs > 0,
    },
    {
      key: "lhu", icon: Upload, to: "/vault", cta: "Unggah LHU",
      title: "Unggah LHU pertama",
      desc: "Upload hasil uji + nilai parameter. Jadwal berikutnya dihitung otomatis.",
      done: st.tested,
    },
    ...(canInvite ? [{
      key: "team", icon: Users, to: "/tim", cta: "Undang Tim", optional: true,
      title: "Undang tim Anda",
      desc: "Ajak HRGA/PIC & Supervisor agar ikut menerima pengingat.",
      done: false,
    }] : []),
  ];

  const required = steps.filter((s) => !s.optional);
  const doneRequired = required.filter((s) => s.done).length;
  const allDone = doneRequired === required.length;
  const nextStep = steps.find((s) => !s.done);

  if (allDone && onReady) {
    // let parent re-render the real dashboard
    onReady();
  }

  return (
    <div className="animate-fade-up space-y-6" data-testid="onboarding">
      <div className="rounded-2xl bg-[#064E3B] text-white p-7 relative overflow-hidden">
        <div className="absolute -right-16 -top-16 h-56 w-56 rounded-full bg-emerald-400/10" />
        <div className="relative">
          <div className="flex items-center gap-2 text-emerald-200 text-sm">
            <Sparkles className="h-4 w-4" /> Selamat datang, {user.name?.split(" ")[0] || "rekan"}!
          </div>
          <h1 className="font-head text-2xl sm:text-3xl font-bold mt-2">Ayo siapkan PATUH dalam 4 langkah</h1>
          <p className="text-emerald-100/80 mt-2 max-w-xl text-sm sm:text-base">
            Setelah ini, PATUH otomatis memantau jadwal uji air limbah & emisi Anda dan mengingatkan sebelum jatuh tempo.
          </p>
          <div className="mt-5 flex items-center gap-3">
            <div className="flex-1 max-w-xs h-2.5 rounded-full bg-white/15 overflow-hidden">
              <div className="h-full bg-emerald-400 rounded-full transition-all" style={{ width: `${(doneRequired / required.length) * 100}%` }} />
            </div>
            <span className="text-sm text-emerald-100">{doneRequired}/{required.length} langkah wajib</span>
          </div>
        </div>
      </div>

      <div className="grid gap-3">
        {steps.map((s, i) => {
          const isNext = nextStep && s.key === nextStep.key;
          return (
            <div
              key={s.key}
              data-testid={`onboarding-step-${s.key}`}
              className={`flex items-center gap-4 rounded-2xl border p-4 sm:p-5 bg-white transition-all ${
                isNext ? "border-emerald-400 ring-2 ring-emerald-100" : "border-slate-200"
              }`}
            >
              <div className={`h-11 w-11 rounded-xl grid place-items-center shrink-0 ${s.done ? "bg-emerald-100" : "bg-slate-100"}`}>
                <s.icon className={`h-5 w-5 ${s.done ? "text-emerald-700" : "text-slate-500"}`} />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-slate-400">LANGKAH {i + 1}</span>
                  {s.optional && <span className="text-[10px] uppercase tracking-wide text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">opsional</span>}
                </div>
                <div className="font-head font-semibold text-emerald-950">{s.title}</div>
                <div className="text-sm text-slate-500">{s.desc}</div>
              </div>
              <div className="shrink-0">
                {s.done ? (
                  <span className="inline-flex items-center gap-1 text-emerald-700 text-sm font-semibold"><CheckCircle2 className="h-5 w-5" /> Selesai</span>
                ) : (
                  <Link to={s.to}>
                    <Button data-testid={`onboarding-cta-${s.key}`} className={isNext ? "bg-[#064E3B] hover:bg-[#022C22] text-white" : "bg-white border border-slate-200 text-emerald-800 hover:bg-emerald-50"}>
                      {s.cta} <ArrowRight className="h-4 w-4 ml-1" />
                    </Button>
                  </Link>
                )}
              </div>
              {!s.done && !isNext && <Circle className="h-4 w-4 text-slate-300 hidden sm:block" />}
            </div>
          );
        })}
      </div>

      {allDone && (
        <div className="rounded-2xl border-2 border-emerald-200 bg-emerald-50 p-5 flex items-center gap-3" data-testid="onboarding-complete">
          <PartyPopper className="h-7 w-7 text-emerald-600" />
          <div>
            <div className="font-head font-bold text-emerald-800">Setup dasar selesai!</div>
            <div className="text-sm text-emerald-700/80">Dashboard Anda kini aktif memantau jadwal pengujian.</div>
          </div>
        </div>
      )}
    </div>
  );
}
