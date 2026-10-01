import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { ROLE_LABEL } from "@/lib/helpers";
import {
  LayoutDashboard, MapPin, FolderArchive, FlaskConical, TrendingUp,
  Users, Bell, Shield, LogOut, Leaf, ChevronDown,
} from "lucide-react";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/sites", label: "Site & Titik Uji", icon: MapPin },
  { to: "/vault", label: "Vault LHU", icon: FolderArchive },
  { to: "/lab", label: "Direktori Lab", icon: FlaskConical },
  { to: "/analitik", label: "Skor & Tren", icon: TrendingUp },
  { to: "/tim", label: "Tim & Undangan", icon: Users, roles: ["company_admin", "swarna_admin"] },
  { to: "/notifikasi", label: "Log Pengingat", icon: Bell },
  { to: "/admin", label: "Admin Swarna", icon: Shield, roles: ["swarna_admin"] },
];

export default function Layout({ children }) {
  const { user, logout, companies, companyId, switchCompany } = useAuth();
  const navigate = useNavigate();
  const activeCompany = companies.find((c) => c.id === companyId);
  const items = NAV.filter((n) => !n.roles || n.roles.includes(user.role));

  return (
    <div className="min-h-screen flex bg-[#F8FAFC]">
      <aside className="w-64 shrink-0 bg-[#064E3B] text-white flex-col hidden md:flex sticky top-0 h-screen">
        <div className="px-6 py-6 flex items-center gap-2 border-b border-white/10">
          <div className="h-9 w-9 rounded-xl bg-emerald-400/20 grid place-items-center">
            <Leaf className="h-5 w-5 text-emerald-300" />
          </div>
          <div>
            <div className="font-head font-bold leading-tight">Swarna</div>
            <div className="text-[11px] text-emerald-200/80 tracking-wide">PROPER Tracker</div>
          </div>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {items.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.end}
              data-testid={`nav-${n.to === "/" ? "dashboard" : n.to.slice(1)}`}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive ? "bg-white text-emerald-900" : "text-emerald-100 hover:bg-white/10 hover:text-white"
                }`
              }
            >
              <n.icon className="h-[18px] w-[18px]" />
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="px-4 py-4 border-t border-white/10 text-xs text-emerald-200/70">
          {ROLE_LABEL[user.role]}
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 bg-white/95 backdrop-blur border-b border-slate-200 flex items-center justify-between px-5 sticky top-0 z-20">
          <div className="flex items-center gap-3">
            {companies.length > 0 && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button
                    data-testid="company-switcher"
                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-sm font-semibold text-emerald-900"
                  >
                    <span className="truncate max-w-[200px]">{activeCompany?.name || "Pilih Perusahaan"}</span>
                    <ChevronDown className="h-4 w-4 text-slate-400" />
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start" className="bg-white">
                  {companies.map((c) => (
                    <DropdownMenuItem
                      key={c.id}
                      data-testid={`company-option-${c.id}`}
                      onClick={() => c.id !== companyId && switchCompany(c.id)}
                      className="cursor-pointer"
                    >
                      {c.name}
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block">
              <div className="text-sm font-semibold text-emerald-900 leading-tight">{user.name}</div>
              <div className="text-[11px] text-slate-500">{user.email}</div>
            </div>
            <button
              data-testid="logout-button"
              onClick={() => { logout(); navigate("/login"); }}
              className="h-9 w-9 grid place-items-center rounded-lg border border-slate-200 text-slate-500 hover:bg-red-50 hover:text-red-600 hover:border-red-200 transition-colors"
              title="Keluar"
            >
              <LogOut className="h-[18px] w-[18px]" />
            </button>
          </div>
        </header>
        <main className="flex-1 p-5 sm:p-8 max-w-[1400px] w-full mx-auto">{children}</main>
      </div>
    </div>
  );
}
