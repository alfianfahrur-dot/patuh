import { useEffect, useState } from "react";
import { toast } from "sonner";
import api, { apiError } from "@/lib/api";
import { formatDate } from "@/lib/helpers";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter,
} from "@/components/ui/dialog";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Building2, Plus, Copy, MessageCircle, Send, Shield, FlaskConical, CheckCircle2, Database } from "lucide-react";

export default function Admin() {
  const [companies, setCompanies] = useState([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: "", admin_email: "", admin_name: "" });
  const [lastLink, setLastLink] = useState("");
  const [wa, setWa] = useState({ enabled: false, api_url: "", api_key: "", sender_number: "", configured: false });
  const [sending, setSending] = useState(false);
  const [bmStd, setBmStd] = useState([]);
  const [bmOnlyVerif, setBmOnlyVerif] = useState(false);
  const [bmAudit, setBmAudit] = useState([]);
  const [seeding, setSeeding] = useState(false);

  const loadBakuMutu = async () => {
    try {
      const params = bmOnlyVerif ? { perlu_verifikasi: true } : {};
      const [s, a] = await Promise.all([
        api.get("/admin/baku-mutu/standar", { params }),
        api.get("/admin/baku-mutu/audit"),
      ]);
      setBmStd(s.data); setBmAudit(a.data);
    } catch (e) { toast.error(apiError(e)); }
  };
  useEffect(() => { loadBakuMutu(); }, [bmOnlyVerif]);

  const runSeed = async () => {
    setSeeding(true);
    try {
      const { data } = await api.post("/admin/baku-mutu/seed");
      toast.success(`Seed selesai: ${data.total_standar} standar, ${data.total_regulasi} regulasi (ditambah ${data.standar_ditambah}, diubah ${data.standar_diubah}).`);
      loadBakuMutu();
    } catch (e) { toast.error(apiError(e)); }
    finally { setSeeding(false); }
  };

  const verifyStandar = async (id) => {
    try {
      await api.post(`/admin/baku-mutu/standar/${id}/verifikasi`);
      toast.success("Standar ditandai terverifikasi");
      loadBakuMutu();
    } catch (e) { toast.error(apiError(e)); }
  };

  const load = async () => {
    const [c, w] = await Promise.all([api.get("/companies"), api.get("/settings/whatsapp")]);
    setCompanies(c.data); setWa(w.data);
  };
  useEffect(() => { load(); }, []);

  const createCompany = async () => {
    if (!form.name || !form.admin_email) { toast.error("Lengkapi nama & email admin klien"); return; }
    try {
      const { data } = await api.post("/companies", form);
      toast.success("Perusahaan dibuat & undangan terkirim");
      setLastLink(data.invite_link);
      setForm({ name: "", admin_email: "", admin_name: "" });
      load();
    } catch (e) { toast.error(apiError(e)); }
  };

  const saveWa = async () => {
    try {
      const { data } = await api.put("/settings/whatsapp", {
        enabled: wa.enabled, api_url: wa.api_url, sender_number: wa.sender_number,
        api_key: wa.api_key === "****" ? "" : wa.api_key,
      });
      setWa(data);
      toast.success("Konfigurasi WhatsApp disimpan");
    } catch (e) { toast.error(apiError(e)); }
  };

  const runReminders = async () => {
    setSending(true);
    try {
      const { data } = await api.post("/reminders/run-now");
      toast.success(`Pengecekan selesai. ${data.emails_attempted} email reminder diproses.`);
    } catch (e) { toast.error(apiError(e)); }
    finally { setSending(false); }
  };

  const copy = (t) => { navigator.clipboard.writeText(t); toast.success("Link disalin"); };

  return (
    <div className="animate-fade-up space-y-6">
      <div className="flex items-center gap-2">
        <Shield className="h-7 w-7 text-emerald-700" />
        <div>
          <h1 className="font-head text-3xl font-bold text-emerald-950">Panel Admin PATUH</h1>
          <p className="text-slate-500">Kelola perusahaan klien, undangan, dan konfigurasi pengingat.</p>
        </div>
      </div>

      <Tabs defaultValue="companies">
        <TabsList>
          <TabsTrigger value="companies" data-testid="tab-companies">Perusahaan</TabsTrigger>
          <TabsTrigger value="whatsapp" data-testid="tab-whatsapp">WhatsApp Gateway</TabsTrigger>
          <TabsTrigger value="reminders" data-testid="tab-reminders">Pengingat</TabsTrigger>
          <TabsTrigger value="bakumutu" data-testid="tab-bakumutu">Baku Mutu</TabsTrigger>
        </TabsList>

        <TabsContent value="companies" className="mt-5 space-y-4">
          <div className="flex justify-end">
            <Dialog open={open} onOpenChange={setOpen}>
              <DialogTrigger asChild>
                <Button data-testid="add-company-button" className="bg-[#064E3B] hover:bg-[#022C22] text-white"><Plus className="h-4 w-4 mr-1" /> Perusahaan Baru</Button>
              </DialogTrigger>
              <DialogContent className="bg-white">
                <DialogHeader><DialogTitle className="font-head text-emerald-950">Buat Perusahaan & Undang Admin Klien</DialogTitle></DialogHeader>
                <div className="space-y-3">
                  <div><Label>Nama Perusahaan</Label><Input data-testid="company-name-input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="PT Hijau Lestari" className="mt-1" /></div>
                  <div><Label>Email Admin Klien</Label><Input data-testid="company-admin-email-input" type="email" value={form.admin_email} onChange={(e) => setForm({ ...form, admin_email: e.target.value })} className="mt-1" /></div>
                  <div><Label>Nama Admin Klien (opsional)</Label><Input data-testid="company-admin-name-input" value={form.admin_name} onChange={(e) => setForm({ ...form, admin_name: e.target.value })} className="mt-1" /></div>
                  {lastLink && (
                    <div className="bg-emerald-50 rounded-lg p-3 text-xs">
                      <div className="text-emerald-800 font-medium mb-1">Link undangan admin:</div>
                      <div className="flex items-center gap-2"><code className="truncate text-slate-600 flex-1">{lastLink}</code><button onClick={() => copy(lastLink)} className="text-emerald-700"><Copy className="h-4 w-4" /></button></div>
                    </div>
                  )}
                </div>
                <DialogFooter><Button data-testid="save-company-button" onClick={createCompany} className="bg-[#064E3B] text-white">Buat & Kirim Undangan</Button></DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="companies-list">
            {companies.length === 0 && <p className="text-slate-400 text-sm">Belum ada perusahaan yang Anda pegang.</p>}
            {companies.map((c) => (
              <div key={c.id} className="bg-white rounded-2xl border border-slate-200 p-5" data-testid={`company-${c.id}`}>
                <div className="h-11 w-11 rounded-xl bg-emerald-50 grid place-items-center mb-3"><Building2 className="h-5 w-5 text-emerald-700" /></div>
                <div className="font-head font-semibold text-emerald-950">{c.name}</div>
                <div className="text-xs text-slate-500 mt-0.5">Dibuat {formatDate(c.created_at)}</div>
                <Badge className={`mt-3 ${c.status_pendaftaran === "aktif" ? "bg-emerald-100 text-emerald-800 hover:bg-emerald-100" : "bg-amber-100 text-amber-800 hover:bg-amber-100"}`}>
                  {c.status_pendaftaran === "aktif" ? "Aktif" : "Menunggu aktivasi"}
                </Badge>
              </div>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="whatsapp" className="mt-5">
          <div className="bg-white rounded-2xl border border-slate-200 p-6 max-w-2xl space-y-4">
            <div className="flex items-center gap-2">
              <MessageCircle className="h-5 w-5 text-emerald-700" />
              <h2 className="font-head font-semibold text-emerald-950">Konfigurasi WhatsApp Gateway</h2>
            </div>
            {!wa.configured && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 text-sm text-amber-800" data-testid="wa-status">
                WhatsApp belum dikonfigurasi. Sistem tetap berjalan normal dengan pengingat <strong>email saja</strong>.
              </div>
            )}
            {wa.configured && (
              <div className="bg-emerald-50 border border-emerald-200 rounded-lg px-4 py-3 text-sm text-emerald-800" data-testid="wa-status">
                WhatsApp aktif. Pengingat akan dikirim lewat email dan WhatsApp.
              </div>
            )}
            <div className="flex items-center justify-between rounded-lg border border-slate-200 px-4 py-3">
              <div><div className="text-sm font-medium text-emerald-900">Aktifkan WhatsApp</div><div className="text-xs text-slate-500">Butuh API URL & API Key terisi</div></div>
              <Switch data-testid="wa-enabled-switch" checked={wa.enabled} onCheckedChange={(v) => setWa({ ...wa, enabled: v })} />
            </div>
            <div><Label>API URL Provider (webhook/endpoint)</Label><Input data-testid="wa-url-input" value={wa.api_url || ""} onChange={(e) => setWa({ ...wa, api_url: e.target.value })} placeholder="https://provider-wa.com/api/send" className="mt-1" /></div>
            <div><Label>API Key</Label><Input data-testid="wa-key-input" value={wa.api_key || ""} onChange={(e) => setWa({ ...wa, api_key: e.target.value })} placeholder="masukkan API key" className="mt-1" /></div>
            <div><Label>Nomor Pengirim</Label><Input data-testid="wa-sender-input" value={wa.sender_number || ""} onChange={(e) => setWa({ ...wa, sender_number: e.target.value })} placeholder="628xxxxxxxxxx" className="mt-1" /></div>
            <Button data-testid="save-wa-button" onClick={saveWa} className="bg-[#064E3B] text-white">Simpan Konfigurasi</Button>
          </div>
        </TabsContent>

        <TabsContent value="reminders" className="mt-5">
          <div className="bg-white rounded-2xl border border-slate-200 p-6 max-w-2xl space-y-4">
            <h2 className="font-head font-semibold text-emerald-950">Mesin Pengingat</h2>
            <p className="text-sm text-slate-600">
              Pengingat otomatis dikirim setiap hari (H-30, H-14, H-7, dan hari-H) ke HRGA/PIC klien dan Admin PATUH yang ditugaskan.
              Anda bisa menjalankan pengecekan manual sekarang untuk menguji.
            </p>
            <Button data-testid="run-reminders-button" onClick={runReminders} disabled={sending} className="bg-[#064E3B] text-white">
              <Send className="h-4 w-4 mr-1" /> {sending ? "Memproses…" : "Jalankan Pengecekan Sekarang"}
            </Button>
          </div>
        </TabsContent>

        <TabsContent value="bakumutu" className="mt-5 space-y-4">
          <div className="bg-white rounded-2xl border border-slate-200 p-5">
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-2">
                <Database className="h-5 w-5 text-emerald-700" />
                <div>
                  <h2 className="font-head font-semibold text-emerald-950">Pustaka Baku Mutu</h2>
                  <p className="text-xs text-slate-500">{bmStd.length} standar dimuat. Jalankan seed untuk memuat/memperbarui dari peraturan.</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button size="sm" variant="outline" onClick={() => setBmOnlyVerif((v) => !v)} data-testid="bm-filter-verif">
                  {bmOnlyVerif ? "Tampilkan semua" : "Hanya perlu verifikasi"}
                </Button>
                <Button size="sm" onClick={runSeed} disabled={seeding} data-testid="bm-seed-button" className="bg-[#064E3B] hover:bg-[#022C22] text-white">
                  {seeding ? "Menyeed…" : "Jalankan Seed"}
                </Button>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden" data-testid="bm-standar-list">
            <div className="max-h-[480px] overflow-y-auto divide-y divide-slate-100">
              {bmStd.length === 0 && <p className="text-sm text-slate-400 p-5">Belum ada standar. Jalankan seed terlebih dahulu.</p>}
              {bmStd.map((s) => (
                <div key={s.id} className="px-4 py-3 flex items-start justify-between gap-3" data-testid={`bm-std-${s.id}`}>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <FlaskConical className="h-4 w-4 text-emerald-700 shrink-0" />
                      <span className="font-semibold text-emerald-950 text-sm">{s.sektor}</span>
                      <Badge className="bg-slate-100 text-slate-600 text-[10px]">{s.kategori}</Badge>
                      {s.perlu_verifikasi
                        ? <Badge className="bg-amber-100 text-amber-800 text-[10px]">Perlu verifikasi</Badge>
                        : <Badge className="bg-emerald-100 text-emerald-800 text-[10px]">Terverifikasi/OK</Badge>}
                    </div>
                    <div className="text-xs text-slate-500 mt-0.5">{s.sub_kategori}</div>
                    <div className="text-[11px] text-slate-400 mt-0.5">{s.regulasi?.judul} · {(s.parameter || []).length} parameter</div>
                    {s.diverifikasi_pada && <div className="text-[11px] text-emerald-600 mt-0.5">Diverifikasi oleh {s.diverifikasi_oleh}</div>}
                  </div>
                  {s.perlu_verifikasi && (
                    <Button size="sm" variant="outline" onClick={() => verifyStandar(s.id)} data-testid={`bm-verify-${s.id}`} className="shrink-0">
                      <CheckCircle2 className="h-4 w-4 mr-1" /> Verifikasi
                    </Button>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 p-5">
            <h3 className="font-head font-semibold text-emerald-950 text-sm mb-2">Riwayat Perubahan (Audit)</h3>
            {bmAudit.length === 0 && <p className="text-xs text-slate-400">Belum ada aktivitas.</p>}
            <div className="space-y-1.5 max-h-[220px] overflow-y-auto">
              {bmAudit.map((a) => (
                <div key={a.id} className="text-xs text-slate-600 flex items-center gap-2" data-testid={`bm-audit-${a.id}`}>
                  <Badge className="bg-slate-100 text-slate-600 text-[10px]">{a.aksi}</Badge>
                  <span className="font-medium">{a.standar_id}</span>
                  <span className="text-slate-400">oleh {a.oleh} · {formatDate(a.pada)}</span>
                </div>
              ))}
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
