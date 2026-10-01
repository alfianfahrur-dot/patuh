import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { toast } from "sonner";
import api, { apiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Leaf, XCircle } from "lucide-react";

export default function ResetPassword() {
  const { token } = useParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState("checking");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api.get(`/auth/validate-reset/${token}`)
      .then(({ data }) => { setEmail(data.email); setStatus("ok"); })
      .catch((e) => { setError(apiError(e)); setStatus("invalid"); });
  }, [token]);

  const submit = async (e) => {
    e.preventDefault();
    if (password !== confirm) { setError("Konfirmasi kata sandi tidak cocok"); return; }
    if (password.length < 6) { setError("Kata sandi minimal 6 karakter"); return; }
    setSubmitting(true); setError("");
    try {
      await api.post("/auth/reset-password", { token, password });
      toast.success("Kata sandi berhasil diperbarui. Silakan masuk.");
      navigate("/login");
    } catch (err) {
      setError(apiError(err));
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-[#064E3B]">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl p-8" data-testid="reset-card">
        <div className="flex items-center gap-2 mb-6">
          <div className="h-10 w-10 rounded-xl bg-emerald-100 grid place-items-center"><Leaf className="h-5 w-5 text-emerald-700" /></div>
          <span className="font-head font-bold text-emerald-950 text-lg">PATUH</span>
        </div>

        {status === "checking" && <p className="text-slate-500" data-testid="reset-checking">Memeriksa tautan…</p>}

        {status === "invalid" && (
          <div data-testid="reset-invalid">
            <XCircle className="h-14 w-14 text-red-500 mb-3" />
            <h2 className="font-head text-xl font-bold text-red-700">Tautan Tidak Berlaku</h2>
            <p className="text-slate-600 text-sm mt-2">{error}</p>
            <Link to="/forgot-password"><Button className="mt-5 bg-[#064E3B] text-white" data-testid="reset-request-new">Minta Tautan Baru</Button></Link>
          </div>
        )}

        {status === "ok" && (
          <form onSubmit={submit} data-testid="reset-form">
            <h2 className="font-head text-xl font-bold text-emerald-950">Buat kata sandi baru</h2>
            <p className="text-slate-500 text-sm mt-1 mb-5">Untuk akun <strong className="text-emerald-900">{email}</strong></p>
            {error && <div className="mb-4 text-sm bg-[#FEF2F2] text-[#991B1B] border border-[#FCA5A5] rounded-lg px-4 py-2.5">{error}</div>}
            <div className="space-y-3.5">
              <div>
                <Label className="text-emerald-900">Kata Sandi Baru</Label>
                <Input data-testid="reset-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required className="mt-1" />
              </div>
              <div>
                <Label className="text-emerald-900">Konfirmasi Kata Sandi</Label>
                <Input data-testid="reset-confirm" type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required className="mt-1" />
              </div>
            </div>
            <Button type="submit" data-testid="reset-submit" disabled={submitting} className="w-full mt-6 bg-[#064E3B] hover:bg-[#022C22] text-white h-11">
              {submitting ? "Menyimpan…" : "Simpan Kata Sandi Baru"}
            </Button>
          </form>
        )}
      </div>
    </div>
  );
}
