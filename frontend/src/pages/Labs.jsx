import { useEffect, useState } from "react";
import { toast } from "sonner";
import api, { apiError } from "@/lib/api";
import { formatDate } from "@/lib/helpers";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter,
} from "@/components/ui/dialog";
import { FlaskConical, Plus, Phone, MessageCircle, Trash2, Pencil, BadgeCheck } from "lucide-react";

const empty = { nama: "", akreditasi_kan: false, narahubung: "", no_hp: "", catatan: "" };

export default function Labs() {
  const [labs, setLabs] = useState([]);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(empty);
  const company = JSON.parse(localStorage.getItem("swarna_company_name") || "null");

  const load = async () => setLabs((await api.get("/labs")).data);
  useEffect(() => { load(); }, []);

  const openNew = () => { setEditing(null); setForm(empty); setOpen(true); };
  const openEdit = (l) => { setEditing(l.id); setForm({ nama: l.nama, akreditasi_kan: l.akreditasi_kan, narahubung: l.narahubung || "", no_hp: l.no_hp || "", catatan: l.catatan || "" }); setOpen(true); };

  const save = async () => {
    if (!form.nama) { toast.error("Nama lab wajib diisi"); return; }
    try {
      if (editing) await api.put(`/labs/${editing}`, form);
      else await api.post("/labs", form);
      toast.success(editing ? "Lab diperbarui" : "Lab ditambahkan");
      setOpen(false); load();
    } catch (e) { toast.error(apiError(e)); }
  };

  const del = async (id) => { if (!window.confirm("Hapus lab ini?")) return; await api.delete(`/labs/${id}`); toast.success("Lab dihapus"); load(); };

  const waLink = (hp) => {
    const num = (hp || "").replace(/[^0-9]/g, "").replace(/^0/, "62");
    const msg = encodeURIComponent(`Halo, kami ingin menjadwalkan pengambilan sampel pengujian lingkungan (PROPER). Mohon info ketersediaan jadwalnya. Terima kasih.`);
    return `https://wa.me/${num}?text=${msg}`;
  };

  return (
    <div className="animate-fade-up space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="font-head text-3xl font-bold text-emerald-950">Direktori Laboratorium</h1>
          <p className="text-slate-500 mt-1">Simpan kontak lab langganan. Hubungi lewat WhatsApp/telepon dengan satu klik.</p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button data-testid="add-lab-button" onClick={openNew} className="bg-[#064E3B] hover:bg-[#022C22] text-white"><Plus className="h-4 w-4 mr-1" /> Tambah Lab</Button>
          </DialogTrigger>
          <DialogContent className="bg-white">
            <DialogHeader><DialogTitle className="font-head text-emerald-950">{editing ? "Edit Lab" : "Tambah Lab"}</DialogTitle></DialogHeader>
            <div className="space-y-3">
              <div><Label>Nama Laboratorium</Label><Input data-testid="lab-name-input" value={form.nama} onChange={(e) => setForm({ ...form, nama: e.target.value })} className="mt-1" /></div>
              <div className="flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2">
                <div><div className="text-sm font-medium text-emerald-900">Terakreditasi KAN</div><div className="text-xs text-slate-500">Komite Akreditasi Nasional</div></div>
                <Switch data-testid="lab-kan-switch" checked={form.akreditasi_kan} onCheckedChange={(v) => setForm({ ...form, akreditasi_kan: v })} />
              </div>
              <div><Label>Nama Sales / Narahubung</Label><Input data-testid="lab-contact-input" value={form.narahubung} onChange={(e) => setForm({ ...form, narahubung: e.target.value })} className="mt-1" /></div>
              <div><Label>No. HP / WhatsApp</Label><Input data-testid="lab-phone-input" value={form.no_hp} onChange={(e) => setForm({ ...form, no_hp: e.target.value })} placeholder="08xxxxxxxxxx" className="mt-1" /></div>
              <div><Label>Catatan</Label><Textarea data-testid="lab-notes-input" value={form.catatan} onChange={(e) => setForm({ ...form, catatan: e.target.value })} className="mt-1" /></div>
            </div>
            <DialogFooter><Button data-testid="save-lab-button" onClick={save} className="bg-[#064E3B] text-white">Simpan</Button></DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {labs.length === 0 ? (
        <div className="bg-white border border-dashed border-slate-300 rounded-2xl p-10 text-center">
          <FlaskConical className="h-10 w-10 text-slate-300 mx-auto mb-3" />
          <p className="text-slate-500">Belum ada lab tersimpan.</p>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {labs.map((l) => (
            <div key={l.id} className="bg-white rounded-2xl border border-slate-200 p-5 flex flex-col" data-testid={`lab-${l.id}`}>
              <div className="flex items-start justify-between">
                <div className="h-11 w-11 rounded-xl bg-emerald-50 grid place-items-center"><FlaskConical className="h-5 w-5 text-emerald-700" /></div>
                <div className="flex gap-1">
                  <button onClick={() => openEdit(l)} data-testid={`edit-lab-${l.id}`} className="h-8 w-8 grid place-items-center rounded-lg text-slate-400 hover:bg-slate-100"><Pencil className="h-4 w-4" /></button>
                  <button onClick={() => del(l.id)} data-testid={`delete-lab-${l.id}`} className="h-8 w-8 grid place-items-center rounded-lg text-slate-400 hover:bg-red-50 hover:text-red-600"><Trash2 className="h-4 w-4" /></button>
                </div>
              </div>
              <div className="mt-3 font-head font-semibold text-emerald-950">{l.nama}</div>
              {l.akreditasi_kan && <Badge className="w-fit mt-1 bg-blue-100 text-blue-800 hover:bg-blue-100"><BadgeCheck className="h-3 w-3 mr-1" /> Terakreditasi KAN</Badge>}
              <div className="text-sm text-slate-500 mt-2 space-y-0.5">
                {l.narahubung && <div>Narahubung: <span className="text-slate-700">{l.narahubung}</span></div>}
                {l.no_hp && <div className="font-mono-data text-slate-700">{l.no_hp}</div>}
                {l.last_used && <div className="text-xs text-slate-400">Terakhir dipakai: {formatDate(l.last_used)}</div>}
              </div>
              {l.catatan && <div className="text-xs text-slate-400 mt-2">{l.catatan}</div>}
              {l.no_hp && (
                <div className="mt-4 flex gap-2">
                  <a href={waLink(l.no_hp)} target="_blank" rel="noreferrer" data-testid={`wa-lab-${l.id}`} className="flex-1 inline-flex items-center justify-center gap-1.5 h-9 rounded-lg bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 transition-colors"><MessageCircle className="h-4 w-4" /> Hubungi WA</a>
                  <a href={`tel:${l.no_hp}`} data-testid={`call-lab-${l.id}`} className="h-9 w-9 inline-flex items-center justify-center rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50"><Phone className="h-4 w-4" /></a>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
