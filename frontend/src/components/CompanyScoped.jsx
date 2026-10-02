import { Link } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Building2, ShieldCheck, Mail } from "lucide-react";

function NoCompanyGate({ role }) {
  const isSwarnaAdmin = role === "swarna_admin";
  return (
    <div className="animate-fade-up min-h-[60vh] grid place-items-center" data-testid="no-company-gate">
      <div className="max-w-lg w-full bg-white rounded-2xl border border-slate-200 p-8 text-center">
        <div className="h-14 w-14 rounded-2xl bg-emerald-50 grid place-items-center mx-auto mb-4">
          <Building2 className="h-7 w-7 text-emerald-700" />
        </div>
        {isSwarnaAdmin ? (
          <>
            <h2 className="font-head text-2xl font-bold text-emerald-950">Belum ada perusahaan</h2>
            <p className="text-slate-500 mt-2">
              Anda belum memegang perusahaan mana pun. Buat perusahaan klien pertama Anda di
              Panel Admin PATUH untuk mulai mengelola site, titik uji, dan vault LHU.
            </p>
            <Link
              to="/admin"
              data-testid="gate-goto-admin"
              className="inline-flex items-center gap-2 mt-6 px-5 py-2.5 rounded-lg bg-[#064E3B] hover:bg-[#022C22] text-white text-sm font-semibold transition-colors"
            >
              <ShieldCheck className="h-4 w-4" /> Buka Admin PATUH
            </Link>
          </>
        ) : (
          <>
            <h2 className="font-head text-2xl font-bold text-emerald-950">Perusahaan belum aktif</h2>
            <p className="text-slate-500 mt-2">
              Akun Anda belum tertaut ke perusahaan mana pun. Silakan hubungi Admin PATUH atau
              admin perusahaan Anda untuk mendapatkan akses.
            </p>
            <div className="inline-flex items-center gap-2 mt-6 px-4 py-2 rounded-lg bg-slate-50 text-slate-500 text-sm">
              <Mail className="h-4 w-4" /> Menunggu penautan perusahaan
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default function CompanyScoped({ children }) {
  const { user, companies, companiesLoaded } = useAuth();

  if (!companiesLoaded) {
    return <div className="text-slate-400 animate-pulse" data-testid="scoped-loading">Memuat…</div>;
  }
  if (companies.length === 0) {
    return <NoCompanyGate role={user?.role} />;
  }
  return children;
}
