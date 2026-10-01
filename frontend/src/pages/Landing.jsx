import { Link } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import {
  Leaf, CalendarClock, FolderCheck, FlaskConical, TrendingUp, ShieldCheck, Users,
  ArrowRight, AlertTriangle, Mail, CheckCircle2, Droplets, Factory,
} from "lucide-react";

const HERO_IMG = "https://images.unsplash.com/photo-1569622296640-38737c1d82de?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA2MTJ8MHwxfHNlYXJjaHwyfHxlbnZpcm9ubWVudGFsJTIwbGFib3JhdG9yeSUyMHdhdGVyJTIwdGVzdGluZyUyMG5hdHVyZSUyMGdyZWVuJTIwZm9yZXN0JTIwcHJvZmVzc2lvbmFsJTIwaW5kdXN0cmlhbCUyMGNvbXBsaWFuY2V8ZW58MHx8fHwxNzkwODM0NzA0fDA&ixlib=rb-4.1.0&q=85";
const LAB_IMG = "https://images.unsplash.com/photo-1617155093730-a8bf47be792d?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAzMzV8MHwxfHNlYXJjaHwyfHxsYWJvcmF0b3J5JTIwdGVjaG5pY2lhbiUyMHdhdGVyJTIwc2FtcGxlJTIwdGVzdGluZyUyMHNjaWVuY2V8ZW58MHx8fHwxNzkwODM0NzExfDA&ixlib=rb-4.1.0&q=85";

const FEATURES = [
  { icon: CalendarClock, title: "Pengingat Otomatis", desc: "Reminder H-30, H-14, H-7 & hari-H lewat email ke HRGA dan konsultan — supaya uji berkala tidak pernah telat." },
  { icon: FolderCheck, title: "Vault LHU Rapi", desc: "Semua Laporan Hasil Uji tersimpan kronologis per titik. Tidak ada lagi dokumen 'hilang di email siapa'." },
  { icon: FlaskConical, title: "Direktori Lab", desc: "Simpan kontak lab terakreditasi KAN. Hubungi via WhatsApp satu klik dengan pesan siap kirim." },
  { icon: TrendingUp, title: "Skor & Tren", desc: "Grafik per parameter dengan garis baku mutu. Tahu lebih awal jika ada tren mendekati ambang batas." },
  { icon: ShieldCheck, title: "Data Aman & Terpisah", desc: "Setiap perusahaan hanya melihat datanya sendiri. Keamanan baris-per-baris (Row-Level Security)." },
  { icon: Users, title: "Multi-Peran", desc: "Admin Perusahaan, HRGA/PIC, dan Supervisor bekerja dalam satu tempat sesuai hak aksesnya." },
];

const STEPS = [
  { n: "1", title: "Daftar atau Terima Undangan", desc: "Buat akun perusahaan Anda, atau terima undangan dari konsultan Swarna." },
  { n: "2", title: "Atur Site & Titik Penaatan", desc: "Tentukan outlet IPAL / cerobong, parameter wajib uji, baku mutu, dan frekuensinya." },
  { n: "3", title: "Terima Pengingat & Unggah LHU", desc: "Sistem mengingatkan jadwal uji. Unggah hasil, jadwal berikutnya dihitung otomatis." },
];

function Nav() {
  const { user } = useAuth();
  return (
    <header className="absolute top-0 inset-x-0 z-30">
      <div className="max-w-6xl mx-auto px-6 h-20 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="h-10 w-10 rounded-xl bg-emerald-400/20 grid place-items-center"><Leaf className="h-5 w-5 text-emerald-300" /></div>
          <div className="text-white">
            <div className="font-head font-bold leading-tight">Swarna</div>
            <div className="text-[11px] text-emerald-200/80 tracking-wide">PROPER Tracker</div>
          </div>
        </div>
        <div className="flex items-center gap-2 sm:gap-3">
          {user ? (
            <Link to="/dashboard"><Button data-testid="nav-to-dashboard" className="bg-white text-emerald-900 hover:bg-emerald-50">Buka Dashboard <ArrowRight className="h-4 w-4 ml-1" /></Button></Link>
          ) : (
            <>
              <Link to="/login"><Button data-testid="nav-login" variant="ghost" className="text-white hover:bg-white/10 hover:text-white">Masuk</Button></Link>
              <Link to="/register"><Button data-testid="nav-register" className="bg-emerald-500 hover:bg-emerald-400 text-white">Daftar Gratis</Button></Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}

export default function Landing() {
  return (
    <div className="min-h-screen bg-[#F8FAFC]">
      <Nav />

      {/* HERO */}
      <section className="relative bg-[#064E3B] overflow-hidden">
        <div className="absolute inset-0 opacity-20">
          <img src={HERO_IMG} alt="" className="w-full h-full object-cover" />
        </div>
        <div className="absolute inset-0 bg-gradient-to-b from-[#064E3B]/70 via-[#064E3B]/90 to-[#064E3B]" />
        <div className="absolute -right-32 top-10 h-96 w-96 rounded-full bg-emerald-400/10" />
        <div className="relative max-w-6xl mx-auto px-6 pt-40 pb-28">
          <div className="max-w-2xl animate-fade-up">
            <span className="inline-flex items-center gap-2 text-emerald-200 text-sm bg-white/10 px-3 py-1.5 rounded-full border border-white/10">
              <ShieldCheck className="h-4 w-4" /> Kepatuhan PROPER level Merah & Biru
            </span>
            <h1 className="font-head text-4xl sm:text-5xl lg:text-6xl font-bold text-white leading-[1.1] mt-6">
              Pengujian tidak pernah telat. Dokumen tidak pernah tercecer.
            </h1>
            <p className="text-emerald-100/90 text-base sm:text-lg mt-6 leading-relaxed">
              Asisten kepatuhan lingkungan yang proaktif menuntun staf HRGA — bukan ahli lingkungan —
              memastikan uji air limbah & emisi berkala selalu tepat waktu, dan seluruh LHU tersimpan rapi.
            </p>
            <div className="flex flex-wrap items-center gap-3 mt-8">
              <Link to="/register"><Button data-testid="hero-register" className="bg-emerald-500 hover:bg-emerald-400 text-white h-12 px-7 text-base">Mulai Gratis <ArrowRight className="h-4 w-4 ml-1" /></Button></Link>
              <Link to="/login"><Button data-testid="hero-login" variant="ghost" className="text-white hover:bg-white/10 hover:text-white h-12 px-6 text-base border border-white/20">Masuk ke Akun</Button></Link>
            </div>
            <div className="flex flex-wrap gap-5 mt-8 text-emerald-200/80 text-sm">
              <span className="flex items-center gap-1.5"><CheckCircle2 className="h-4 w-4" /> Tanpa kartu kredit</span>
              <span className="flex items-center gap-1.5"><Mail className="h-4 w-4" /> Reminder via email</span>
              <span className="flex items-center gap-1.5"><ShieldCheck className="h-4 w-4" /> Data terisolasi per perusahaan</span>
            </div>
          </div>
        </div>
      </section>

      {/* PROBLEM */}
      <section className="max-w-6xl mx-auto px-6 py-20">
        <div className="text-center max-w-2xl mx-auto">
          <h2 className="font-head text-3xl font-bold text-emerald-950">Kenapa titik pengujian sering telat?</h2>
          <p className="text-slate-500 mt-3">Tiga masalah klasik yang membuat peringkat PROPER turun — semuanya kami selesaikan.</p>
        </div>
        <div className="grid md:grid-cols-3 gap-5 mt-12">
          {[
            { icon: AlertTriangle, t: "Jadwal tercecer", d: "Tanggal jatuh tempo uji hanya diingat di kepala atau spreadsheet yang mudah terlupakan." },
            { icon: FolderCheck, t: "Dokumen hilang", d: "LHU menyebar di email dan WhatsApp berbagai orang, sulit ditemukan saat audit." },
            { icon: TrendingUp, t: "Tren tak terbaca", d: "Nilai parameter perlahan mendekati baku mutu tanpa ada yang menyadari sampai terlambat." },
          ].map((p) => (
            <div key={p.t} className="bg-white rounded-2xl border border-slate-200 p-6">
              <div className="h-11 w-11 rounded-xl bg-red-50 grid place-items-center"><p.icon className="h-5 w-5 text-red-600" /></div>
              <h3 className="font-head text-lg font-semibold text-emerald-950 mt-4">{p.t}</h3>
              <p className="text-slate-500 text-sm mt-2 leading-relaxed">{p.d}</p>
            </div>
          ))}
        </div>
      </section>

      {/* FEATURES */}
      <section className="bg-white border-y border-slate-200">
        <div className="max-w-6xl mx-auto px-6 py-20">
          <div className="max-w-2xl">
            <span className="text-emerald-600 font-semibold text-sm">FITUR UTAMA</span>
            <h2 className="font-head text-3xl font-bold text-emerald-950 mt-2">Semua yang Anda butuhkan untuk taat PROPER</h2>
            <p className="text-slate-500 mt-3">Dirancang untuk orang sibuk yang tidak familiar istilah teknis — bahasa sederhana, aksi jelas.</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5 mt-12">
            {FEATURES.map((f) => (
              <div key={f.title} className="group rounded-2xl border border-slate-200 p-6 hover:border-emerald-300 hover:shadow-md transition-all">
                <div className="h-12 w-12 rounded-xl bg-emerald-50 grid place-items-center group-hover:bg-emerald-600 transition-colors">
                  <f.icon className="h-6 w-6 text-emerald-700 group-hover:text-white transition-colors" />
                </div>
                <h3 className="font-head text-lg font-semibold text-emerald-950 mt-4">{f.title}</h3>
                <p className="text-slate-500 text-sm mt-2 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SHOWCASE */}
      <section className="max-w-6xl mx-auto px-6 py-20 grid lg:grid-cols-2 gap-12 items-center">
        <div>
          <span className="text-emerald-600 font-semibold text-sm">DASHBOARD YANG MENUNTUN</span>
          <h2 className="font-head text-3xl font-bold text-emerald-950 mt-2">"Apa yang harus saya lakukan sekarang?"</h2>
          <p className="text-slate-500 mt-4 leading-relaxed">
            Begitu masuk, titik yang telat tampil paling atas dengan warna merah tegas, disusul yang jatuh tempo
            dalam 7, 14, dan 30 hari. Tidak perlu menafsirkan grafik rumit — cukup ikuti daftar tindakan.
          </p>
          <ul className="mt-6 space-y-3">
            {[
              [Droplets, "Air limbah & emisi dipantau dalam satu tampilan"],
              [Factory, "Frekuensi uji bisa diatur per titik penaatan"],
              [FlaskConical, "Tombol cepat 'Hubungi Lab' langsung dari daftar jatuh tempo"],
            ].map(([Icon, t]) => (
              <li key={t} className="flex items-center gap-3 text-slate-700">
                <span className="h-8 w-8 rounded-lg bg-emerald-50 grid place-items-center shrink-0"><Icon className="h-4 w-4 text-emerald-700" /></span>
                {t}
              </li>
            ))}
          </ul>
          <Link to="/register"><Button data-testid="showcase-cta" className="mt-8 bg-[#064E3B] hover:bg-[#022C22] text-white h-11 px-6">Coba Sekarang <ArrowRight className="h-4 w-4 ml-1" /></Button></Link>
        </div>
        <div className="relative">
          <div className="absolute -inset-4 bg-emerald-100/50 rounded-3xl -z-10" />
          <img src={LAB_IMG} alt="Teknisi laboratorium menguji sampel air" className="rounded-2xl w-full h-80 object-cover shadow-lg" />
        </div>
      </section>

      {/* STEPS */}
      <section className="bg-[#064E3B]">
        <div className="max-w-6xl mx-auto px-6 py-20">
          <div className="text-center max-w-2xl mx-auto">
            <h2 className="font-head text-3xl font-bold text-white">Tiga langkah, langsung jalan</h2>
            <p className="text-emerald-200/80 mt-3">Tidak butuh pelatihan khusus. Mulai dalam hitungan menit.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-6 mt-12">
            {STEPS.map((s) => (
              <div key={s.n} className="bg-white/5 border border-white/10 rounded-2xl p-6">
                <div className="h-11 w-11 rounded-full bg-emerald-400 text-emerald-950 font-head font-bold grid place-items-center text-lg">{s.n}</div>
                <h3 className="font-head text-lg font-semibold text-white mt-4">{s.title}</h3>
                <p className="text-emerald-100/80 text-sm mt-2 leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-6xl mx-auto px-6 py-20">
        <div className="bg-white rounded-3xl border border-slate-200 p-10 sm:p-14 text-center">
          <h2 className="font-head text-3xl sm:text-4xl font-bold text-emerald-950">Siap jaga peringkat PROPER Anda?</h2>
          <p className="text-slate-500 mt-4 max-w-xl mx-auto">Daftarkan perusahaan Anda hari ini dan biarkan Swarna mengingatkan setiap jadwal uji — otomatis.</p>
          <div className="flex flex-wrap justify-center gap-3 mt-8">
            <Link to="/register"><Button data-testid="cta-register" className="bg-emerald-500 hover:bg-emerald-400 text-white h-12 px-8 text-base">Daftar Gratis</Button></Link>
            <Link to="/login"><Button data-testid="cta-login" variant="outline" className="h-12 px-8 text-base border-emerald-200 text-emerald-800 hover:bg-emerald-50">Masuk</Button></Link>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-slate-200 bg-white">
        <div className="max-w-6xl mx-auto px-6 py-10 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <div className="h-9 w-9 rounded-xl bg-emerald-100 grid place-items-center"><Leaf className="h-4 w-4 text-emerald-700" /></div>
            <span className="font-head font-bold text-emerald-950">Swarna PROPER Tracker</span>
          </div>
          <p className="text-slate-400 text-sm">© 2026 Swarna · Program PROPER (Merah & Biru)</p>
        </div>
      </footer>
    </div>
  );
}
