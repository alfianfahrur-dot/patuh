import { useState } from "react";
import { Link } from "react-router-dom";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Leaf, Mail, ArrowLeft } from "lucide-react";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post("/auth/forgot-password", { email });
      setSent(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-[#064E3B]">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl p-8" data-testid="forgot-card">
        <div className="flex items-center gap-2 mb-6">
          <div className="h-10 w-10 rounded-xl bg-emerald-100 grid place-items-center"><Leaf className="h-5 w-5 text-emerald-700" /></div>
          <span className="font-head font-bold text-emerald-950 text-lg">PATUH</span>
        </div>

        {sent ? (
          <div data-testid="forgot-sent" className="text-center">
            <div className="h-14 w-14 rounded-2xl bg-emerald-100 grid place-items-center mx-auto mb-4"><Mail className="h-7 w-7 text-emerald-700" /></div>
            <h2 className="font-head text-xl font-bold text-emerald-950">Cek email Anda</h2>
            <p className="text-slate-600 text-sm mt-2">
              Jika <strong className="text-emerald-900">{email}</strong> terdaftar, kami mengirim tautan untuk mengatur ulang
              kata sandi. Tautan berlaku 1 jam.
            </p>
            <Link to="/login" className="inline-flex items-center gap-1.5 text-emerald-700 font-semibold hover:underline text-sm mt-5" data-testid="forgot-back-login">
              <ArrowLeft className="h-4 w-4" /> Kembali ke Masuk
            </Link>
          </div>
        ) : (
          <form onSubmit={submit} data-testid="forgot-form">
            <h2 className="font-head text-xl font-bold text-emerald-950">Lupa kata sandi?</h2>
            <p className="text-slate-500 text-sm mt-1 mb-5">Masukkan email akun Anda. Kami akan mengirim tautan pemulihan.</p>
            <div>
              <Label className="text-emerald-900">Email</Label>
              <Input data-testid="forgot-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required className="mt-1" placeholder="nama@perusahaan.com" />
            </div>
            <Button type="submit" data-testid="forgot-submit" disabled={loading} className="w-full mt-6 bg-[#064E3B] hover:bg-[#022C22] text-white h-11">
              {loading ? "Mengirim…" : "Kirim Tautan Reset"}
            </Button>
            <Link to="/login" className="inline-flex items-center gap-1.5 text-slate-500 hover:text-emerald-700 text-sm mt-4" data-testid="forgot-to-login">
              <ArrowLeft className="h-4 w-4" /> Kembali ke Masuk
            </Link>
          </form>
        )}
      </div>
    </div>
  );
}
