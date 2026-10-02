import { useEffect, useState } from "react";
import { toast } from "sonner";
import api, { apiError } from "@/lib/api";
import { ROLE_LABEL, formatDate } from "@/lib/helpers";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter,
} from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Users, UserPlus, Mail, Copy, CheckCircle2, Clock } from "lucide-react";

export default function Team() {
  const { user } = useAuth();
  const [members, setMembers] = useState([]);
  const [invites, setInvites] = useState([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ email: "", name: "", role: "hrga" });
  const [lastLink, setLastLink] = useState("");

  const load = async () => {
    try {
      const [u, i] = await Promise.all([api.get("/users"), api.get("/invitations")]);
      setMembers(u.data); setInvites(i.data);
    } catch (e) { toast.error(apiError(e)); }
  };
  useEffect(() => { load(); }, []);

  const roleOptions = user.role === "company_admin" || user.role === "swarna_admin"
    ? [["hrga", "HRGA / PIC Lingkungan"], ["supervisor", "Supervisor"], ["company_admin", "Admin Perusahaan"]]
    : [["hrga", "HRGA / PIC Lingkungan"]];

  const invite = async () => {
    if (!form.email) { toast.error("Email wajib diisi"); return; }
    try {
      const { data } = await api.post("/invitations", form);
      toast.success("Undangan terkirim via email");
      setLastLink(data.invite_link);
      setForm({ email: "", name: "", role: "hrga" });
      load();
    } catch (e) { toast.error(apiError(e)); }
  };

  const copy = (txt) => { navigator.clipboard.writeText(txt); toast.success("Link undangan disalin"); };

  return (
    <div className="animate-fade-up space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="font-head text-3xl font-bold text-emerald-950">Tim & Undangan</h1>
          <p className="text-slate-500 mt-1">Undang anggota tim perusahaan Anda. Mereka membuat kata sandi sendiri lewat link.</p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button data-testid="invite-member-button" className="bg-[#064E3B] hover:bg-[#022C22] text-white"><UserPlus className="h-4 w-4 mr-1" /> Undang Anggota</Button>
          </DialogTrigger>
          <DialogContent className="bg-white">
            <DialogHeader><DialogTitle className="font-head text-emerald-950">Undang Anggota Tim</DialogTitle></DialogHeader>
            <div className="space-y-3">
              <div><Label>Email</Label><Input data-testid="invite-email-input" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="mt-1" /></div>
              <div><Label>Nama (opsional)</Label><Input data-testid="invite-name-input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="mt-1" /></div>
              <div>
                <Label>Peran</Label>
                <Select value={form.role} onValueChange={(v) => setForm({ ...form, role: v })}>
                  <SelectTrigger data-testid="invite-role-select" className="mt-1"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-white">{roleOptions.map(([v, l]) => <SelectItem key={v} value={v}>{l}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              {lastLink && (
                <div className="bg-emerald-50 rounded-lg p-3 text-xs">
                  <div className="text-emerald-800 font-medium mb-1">Link undangan (cadangan):</div>
                  <div className="flex items-center gap-2">
                    <code className="truncate text-slate-600 flex-1">{lastLink}</code>
                    <button onClick={() => copy(lastLink)} className="text-emerald-700"><Copy className="h-4 w-4" /></button>
                  </div>
                </div>
              )}
            </div>
            <DialogFooter><Button data-testid="send-invite-button" onClick={invite} className="bg-[#064E3B] text-white"><Mail className="h-4 w-4 mr-1" /> Kirim Undangan</Button></DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <section className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2"><Users className="h-5 w-5 text-emerald-700" /><h2 className="font-head font-semibold text-emerald-950">Anggota Aktif ({members.length})</h2></div>
        <div className="divide-y divide-slate-100">
          {members.map((m) => (
            <div key={m.id} className="px-5 py-3 flex items-center justify-between" data-testid={`member-${m.id}`}>
              <div><div className="font-medium text-emerald-950">{m.name}</div><div className="text-xs text-slate-500">{m.email}</div></div>
              <Badge className="bg-emerald-100 text-emerald-800 hover:bg-emerald-100">{ROLE_LABEL[m.role]}</Badge>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2"><Mail className="h-5 w-5 text-amber-600" /><h2 className="font-head font-semibold text-emerald-950">Undangan Terkirim</h2></div>
        <div className="divide-y divide-slate-100">
          {invites.length === 0 && <p className="text-sm text-slate-400 p-5">Belum ada undangan.</p>}
          {invites.map((i) => (
            <div key={i.id} className="px-5 py-3 flex items-center justify-between" data-testid={`invite-${i.id}`}>
              <div><div className="font-medium text-emerald-950">{i.email}</div><div className="text-xs text-slate-500">{ROLE_LABEL[i.role]} · {formatDate(i.created_at)}</div></div>
              <div className="flex items-center gap-2">
                {i.used
                  ? <Badge className="bg-emerald-100 text-emerald-800 hover:bg-emerald-100"><CheckCircle2 className="h-3 w-3 mr-1" /> Diterima</Badge>
                  : <Badge className="bg-amber-100 text-amber-800 hover:bg-amber-100"><Clock className="h-3 w-3 mr-1" /> Menunggu</Badge>}
                {!i.used && <button onClick={() => copy(`${window.location.origin}/invite/${i.token}`)} className="text-slate-400 hover:text-emerald-700"><Copy className="h-4 w-4" /></button>}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
