import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api, { apiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Leaf, ShieldCheck, CalendarClock, FolderCheck } from "lucide-react";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const { data } = await api.post("/auth/login", { email, password });
      await login(data.token, data.user);
      navigate("/dashboard");
    } catch (err) {
      setError(apiError(err, "Gagal masuk"));
    } finally {
      setLoading(false);
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
            <div className="font-head font-bold text-xl">Swarna PROPER Tracker</div>
            <div className="text-emerald-200/80 text-sm">Asisten Kepatuhan Lingkungan</div>
          </div>
        </div>
        <div className="relative space-y-7">
          <h1 className="font-head text-4xl font-bold leading-tight">
            Pengujian tidak pernah telat.<br />Dokumen tidak pernah tercecer.
          </h1>
          {[
            { icon: CalendarClock, t: "Pengingat Otomatis", d: "Reminder H-30, H-14, H-7 & hari-H lewat email." },
            { icon: FolderCheck, t: "Vault LHU Rapi", d: "Semua laporan hasil uji tersimpan kronologis." },
            { icon: ShieldCheck, t: "Data Aman & Terpisah", d: "Tiap perusahaan hanya melihat datanya sendiri." },
          ].map((f) => (
            <div key={f.t} className="flex gap-4">
              <div className="h-10 w-10 rounded-xl bg-white/10 grid place-items-center shrink-0">
                <f.icon className="h-5 w-5 text-emerald-300" />
              </div>
              <div>
                <div className="font-semibold">{f.t}</div>
                <div className="text-emerald-200/80 text-sm">{f.d}</div>
              </div>
            </div>
          ))}
        </div>
        <div className="text-emerald-200/60 text-xs relative">© 2026 Swarna · Program PROPER (Merah & Biru)</div>
      </div>

      <div className="flex-1 flex items-center justify-center p-6 bg-[#F8FAFC]">
        <form onSubmit={submit} className="w-full max-w-sm" data-testid="login-form">
          <h2 className="font-head text-2xl font-bold text-emerald-950">Masuk ke akun Anda</h2>
          <p className="text-slate-500 text-sm mt-1 mb-6">Belum punya akun perusahaan? <Link to="/register" className="text-emerald-700 font-semibold hover:underline" data-testid="to-register-link">Daftar di sini</Link></p>
          {error && (
            <div data-testid="login-error" className="mb-4 text-sm bg-[#FEF2F2] text-[#991B1B] border border-[#FCA5A5] rounded-lg px-4 py-2.5">
              {error}
            </div>
          )}
          <div className="space-y-4">
            <div>
              <Label htmlFor="email" className="text-emerald-900">Email</Label>
              <Input id="email" data-testid="login-email" type="email" value={email}
                onChange={(e) => setEmail(e.target.value)} required className="mt-1" placeholder="nama@perusahaan.com" />
            </div>
            <div>
              <Label htmlFor="password" className="text-emerald-900">Kata Sandi</Label>
              <Input id="password" data-testid="login-password" type="password" value={password}
                onChange={(e) => setPassword(e.target.value)} required className="mt-1" placeholder="••••••••" />
            </div>
          </div>
          <Button type="submit" data-testid="login-submit" disabled={loading}
            className="w-full mt-6 bg-[#064E3B] hover:bg-[#022C22] text-white h-11 text-base">
            {loading ? "Memproses…" : "Masuk"}
          </Button>
        </form>
      </div>
    </div>
  );
}
