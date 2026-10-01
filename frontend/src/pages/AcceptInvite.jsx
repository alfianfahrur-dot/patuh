import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api, { apiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Leaf, CheckCircle2 } from "lucide-react";
import { ROLE_LABEL } from "@/lib/helpers";

export default function AcceptInvite() {
  const { token } = useParams();
  const navigate = useNavigate();
  const { login } = useAuth();
  const [invite, setInvite] = useState(null);
  const [status, setStatus] = useState("loading");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api.get(`/invitations/validate/${token}`)
      .then(({ data }) => { setInvite(data); setStatus("ok"); })
      .catch((e) => { setError(apiError(e)); setStatus("invalid"); });
  }, [token]);

  const submit = async (e) => {
    e.preventDefault();
    if (password !== confirm) { setError("Konfirmasi kata sandi tidak cocok"); return; }
    if (password.length < 6) { setError("Kata sandi minimal 6 karakter"); return; }
    setSubmitting(true);
    setError("");
    try {
      const { data } = await api.post("/invitations/accept", { token, name, password, phone });
      await login(data.token, data.user);
      navigate("/");
    } catch (err) {
      setError(apiError(err));
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-[#064E3B]">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl p-8" data-testid="accept-invite-card">
        <div className="flex items-center gap-2 mb-6">
          <div className="h-10 w-10 rounded-xl bg-emerald-100 grid place-items-center">
            <Leaf className="h-5 w-5 text-emerald-700" />
          </div>
          <span className="font-head font-bold text-emerald-950 text-lg">Swarna PROPER Tracker</span>
        </div>

        {status === "loading" && <p className="text-slate-500">Memeriksa undangan…</p>}

        {status === "invalid" && (
          <div data-testid="invite-invalid">
            <h2 className="font-head text-xl font-bold text-red-700">Undangan Tidak Berlaku</h2>
            <p className="text-slate-600 text-sm mt-2">{error}</p>
            <Button className="mt-5 bg-[#064E3B] text-white" onClick={() => navigate("/login")}>Ke Halaman Masuk</Button>
          </div>
        )}

        {status === "ok" && invite && (
          <form onSubmit={submit} data-testid="invite-form">
            <div className="flex items-center gap-2 text-emerald-700 text-sm mb-1">
              <CheckCircle2 className="h-4 w-4" /> Undangan valid
            </div>
            <h2 className="font-head text-xl font-bold text-emerald-950">Buat kata sandi Anda</h2>
            <p className="text-slate-500 text-sm mt-1 mb-5">
              {invite.email} · {ROLE_LABEL[invite.role] || invite.role_label}
              {invite.company_name ? ` · ${invite.company_name}` : ""}
            </p>
            {error && <div className="mb-4 text-sm bg-[#FEF2F2] text-[#991B1B] border border-[#FCA5A5] rounded-lg px-4 py-2.5">{error}</div>}
            <div className="space-y-3.5">
              <div>
                <Label className="text-emerald-900">Nama Lengkap</Label>
                <Input data-testid="invite-name" value={name} onChange={(e) => setName(e.target.value)} required className="mt-1" />
              </div>
              <div>
                <Label className="text-emerald-900">No. HP / WhatsApp (opsional)</Label>
                <Input data-testid="invite-phone" value={phone} onChange={(e) => setPhone(e.target.value)} className="mt-1" placeholder="628xxxxxxxxxx" />
              </div>
              <div>
                <Label className="text-emerald-900">Kata Sandi</Label>
                <Input data-testid="invite-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required className="mt-1" />
              </div>
              <div>
                <Label className="text-emerald-900">Konfirmasi Kata Sandi</Label>
                <Input data-testid="invite-confirm" type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required className="mt-1" />
              </div>
            </div>
            <Button type="submit" data-testid="invite-submit" disabled={submitting}
              className="w-full mt-6 bg-[#064E3B] hover:bg-[#022C22] text-white h-11">
              {submitting ? "Mengaktifkan…" : "Aktifkan Akun & Masuk"}
            </Button>
          </form>
        )}
      </div>
    </div>
  );
}
