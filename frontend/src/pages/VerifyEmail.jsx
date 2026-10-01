import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import api, { apiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Leaf, CheckCircle2, XCircle } from "lucide-react";

export default function VerifyEmail() {
  const { token } = useParams();
  const navigate = useNavigate();
  const { login } = useAuth();
  const [status, setStatus] = useState("verifying");
  const [error, setError] = useState("");

  useEffect(() => {
    api.get(`/auth/verify-email/${token}`)
      .then(async ({ data }) => {
        setStatus("ok");
        await login(data.token, data.user);
        setTimeout(() => navigate("/dashboard"), 1200);
      })
      .catch((e) => { setError(apiError(e)); setStatus("error"); });
  }, [token]);

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-[#064E3B]">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl p-8 text-center" data-testid="verify-email-card">
        <div className="flex items-center justify-center gap-2 mb-6">
          <div className="h-10 w-10 rounded-xl bg-emerald-100 grid place-items-center"><Leaf className="h-5 w-5 text-emerald-700" /></div>
          <span className="font-head font-bold text-emerald-950 text-lg">Swarna PROPER Tracker</span>
        </div>

        {status === "verifying" && <p className="text-slate-500" data-testid="verify-loading">Memverifikasi email Anda…</p>}

        {status === "ok" && (
          <div data-testid="verify-success">
            <CheckCircle2 className="h-14 w-14 text-emerald-600 mx-auto mb-3" />
            <h2 className="font-head text-xl font-bold text-emerald-950">Email terverifikasi!</h2>
            <p className="text-slate-600 text-sm mt-2">Akun Anda aktif. Mengalihkan ke dashboard…</p>
          </div>
        )}

        {status === "error" && (
          <div data-testid="verify-error">
            <XCircle className="h-14 w-14 text-red-500 mx-auto mb-3" />
            <h2 className="font-head text-xl font-bold text-red-700">Verifikasi Gagal</h2>
            <p className="text-slate-600 text-sm mt-2">{error}</p>
            <Link to="/login"><Button className="mt-5 bg-[#064E3B] text-white" data-testid="verify-to-login">Ke Halaman Masuk</Button></Link>
          </div>
        )}
      </div>
    </div>
  );
}
