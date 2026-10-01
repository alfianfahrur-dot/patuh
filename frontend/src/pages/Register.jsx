import { useState } from "react";
import { Link } from "react-router-dom";
import api, { apiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Leaf, Building2 } from "lucide-react";

export default function Register() {
  const [form, setForm] = useState({ company_name: "", name: "", email: "", phone: "", password: "", confirm: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [resending, setResending] = useState(false);

  const set = (k, v) => setForm({ ...form, [k]: v });

  const submit = async (e) => {
    e.preventDefault();
    if (form.password !== form.confirm) { setError("Konfirmasi kata sandi tidak cocok"); return; }
    if (form.password.length < 6) { setError("Kata sandi minimal 6 karakter"); return; }
    setLoading(true); setError("");
    try {
      await api.post("/auth/register-company", {
        company_name: form.company_name, name: form.name, email: form.email,
        password: form.password, phone: form.phone,
      });
      setSent(true);
    } catch (err) {
      setError(apiError(err, "Gagal mendaftar"));
    } finally {
      setLoading(false);
    }
  };

  const resend = async () => {
    setResending(true);
    try {
      await api.post("/auth/resend-verification", { email: form.email });
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      <div className="hidden lg:flex flex-col justify-between w-[46%] bg-[#064E3B] text-white p-12 relative overflow-hidden">
        <div className="absolute -right-24 -top-24 h-80 w-80 rounded-full bg-emerald-400/10" />
        <div className="absolute -left-20 bottom-10 h-64 w-64 rounded-full bg-emerald-400/10" />
        <div className="flex items-center gap-3 relative">
          <div className="h-11 w-11 rounded-2xl bg-emerald-400/20 grid place-items-center">
            <Leaf className="h-6 w-6 text-emerald-300" />
          </div>
          <div>
            <div className="font-head font-bold text-xl">PATUH</div>
            <div className="text-emerald-200/80 text-sm">Tepat Waktu, Tetap Taat</div>
          </div>
        </div>
        <div className="relative space-y-5">
          <h1 className="font-head text-4xl font-bold leading-tight">
            Daftarkan perusahaan Anda<br />dalam hitungan menit.
          </h1>
          <p className="text-emerald-200/80 text-base leading-relaxed">
            Buat akun perusahaan, atur site & titik penaatan, lalu biarkan sistem mengingatkan
            jadwal uji air limbah & emisi Anda — otomatis lewat email.
          </p>
          <ul className="space-y-2 text-emerald-100/90 text-sm">
            <li>✓ Gratis mulai, tanpa undangan</li>
            <li>✓ Anda otomatis jadi Admin Perusahaan</li>
            <li>✓ Undang tim HRGA Anda sendiri</li>
          </ul>
        </div>
        <div className="text-emerald-200/60 text-xs relative">© 2026 PATUH · Program PROPER (Merah & Biru)</div>
      </div>

      <div className="flex-1 flex items-center justify-center p-6 bg-[#F8FAFC]">
        {sent ? (
          <div className="w-full max-w-sm text-center" data-testid="register-sent">
            <div className="h-14 w-14 rounded-2xl bg-emerald-100 grid place-items-center mx-auto mb-4">
              <Building2 className="h-7 w-7 text-emerald-700" />
            </div>
            <h2 className="font-head text-2xl font-bold text-emerald-950">Cek email Anda</h2>
            <p className="text-slate-600 text-sm mt-2">
              Kami mengirim tautan verifikasi ke <strong className="text-emerald-900">{form.email}</strong>.
              Klik tautan tersebut untuk mengaktifkan akun. Akun belum bisa dipakai sebelum diverifikasi.
            </p>
            <p className="text-slate-400 text-xs mt-3">Tidak menerima email? Cek folder spam, atau kirim ulang.</p>
            <div className="mt-5 flex flex-col gap-2">
              <Button onClick={resend} disabled={resending} data-testid="resend-verification" className="bg-[#064E3B] hover:bg-[#022C22] text-white h-11">
                {resending ? "Mengirim…" : "Kirim Ulang Tautan"}
              </Button>
              <Link to="/login" className="text-emerald-700 font-semibold hover:underline text-sm">Kembali ke halaman Masuk</Link>
            </div>
          </div>
        ) : (
        <form onSubmit={submit} className="w-full max-w-sm" data-testid="register-form">
          <div className="flex items-center gap-2 text-emerald-700 mb-1">
            <Building2 className="h-5 w-5" />
            <span className="text-sm font-medium">Pendaftaran Perusahaan</span>
          </div>
          <h2 className="font-head text-2xl font-bold text-emerald-950">Buat akun baru</h2>
          <p className="text-slate-500 text-sm mt-1 mb-6">Sudah punya akun? <Link to="/login" className="text-emerald-700 font-semibold hover:underline" data-testid="to-login-link">Masuk di sini</Link></p>
          {error && (
            <div data-testid="register-error" className="mb-4 text-sm bg-[#FEF2F2] text-[#991B1B] border border-[#FCA5A5] rounded-lg px-4 py-2.5">{error}</div>
          )}
          <div className="space-y-3.5">
            <div>
              <Label className="text-emerald-900">Nama Perusahaan</Label>
              <Input data-testid="register-company-name" value={form.company_name} onChange={(e) => set("company_name", e.target.value)} required className="mt-1" placeholder="PT Hijau Lestari" />
            </div>
            <div>
              <Label className="text-emerald-900">Nama Anda</Label>
              <Input data-testid="register-name" value={form.name} onChange={(e) => set("name", e.target.value)} required className="mt-1" placeholder="Budi Santoso" />
            </div>
            <div>
              <Label className="text-emerald-900">Email</Label>
              <Input data-testid="register-email" type="email" value={form.email} onChange={(e) => set("email", e.target.value)} required className="mt-1" placeholder="nama@perusahaan.com" />
            </div>
            <div>
              <Label className="text-emerald-900">No. HP / WhatsApp (opsional)</Label>
              <Input data-testid="register-phone" value={form.phone} onChange={(e) => set("phone", e.target.value)} className="mt-1" placeholder="628xxxxxxxxxx" />
            </div>
            <div>
              <Label className="text-emerald-900">Kata Sandi</Label>
              <Input data-testid="register-password" type="password" value={form.password} onChange={(e) => set("password", e.target.value)} required className="mt-1" />
            </div>
            <div>
              <Label className="text-emerald-900">Konfirmasi Kata Sandi</Label>
              <Input data-testid="register-confirm" type="password" value={form.confirm} onChange={(e) => set("confirm", e.target.value)} required className="mt-1" />
            </div>
          </div>
          <Button type="submit" data-testid="register-submit" disabled={loading} className="w-full mt-6 bg-[#064E3B] hover:bg-[#022C22] text-white h-11 text-base">
            {loading ? "Mendaftar…" : "Daftar & Mulai"}
          </Button>
        </form>
        )}
      </div>
    </div>
  );
}
