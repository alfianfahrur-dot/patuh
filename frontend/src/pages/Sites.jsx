import { useEffect, useState } from "react";
import { toast } from "sonner";
import api, { apiError } from "@/lib/api";
import { JENIS_LABEL, JENIS_OPTIONS, FREKUENSI_OPTIONS, dueLabel, dueTone, formatDate } from "@/lib/helpers";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter,
} from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Plus, MapPin, Trash2, Droplets, Factory, X, Pencil } from "lucide-react";

const emptyParam = () => ({ nama: "", satuan: "", baku_mutu: "", baku_mutu_min: "" });

export default function Sites() {
  const [sites, setSites] = useState([]);
  const [points, setPoints] = useState([]);
  const [siteName, setSiteName] = useState("");
  const [siteAddr, setSiteAddr] = useState("");
  const [siteOpen, setSiteOpen] = useState(false);
  const [pointOpen, setPointOpen] = useState(false);
  const [editing, setEditing] = useState(null);

  const [pForm, setPForm] = useState({ site_id: "", name: "", jenis: "air_limbah", frekuensi_bulan: 6, tanggal_uji_terakhir: "", parameters: [emptyParam()] });

  const load = async () => {
    const [s, p] = await Promise.all([api.get("/sites"), api.get("/monitoring-points")]);
    setSites(s.data); setPoints(p.data);
  };
  useEffect(() => { load(); }, []);

  const addSite = async () => {
    if (!siteName) return;
    try {
      await api.post("/sites", { name: siteName, address: siteAddr });
      toast.success("Site ditambahkan");
      setSiteName(""); setSiteAddr(""); setSiteOpen(false); load();
    } catch (e) { toast.error(apiError(e)); }
  };

  const delSite = async (id) => {
    if (!window.confirm("Hapus site ini beserta semua titik penaatannya?")) return;
    await api.delete(`/sites/${id}`); toast.success("Site dihapus"); load();
  };

  const openNewPoint = (siteId) => {
    setEditing(null);
    setPForm({ site_id: siteId || sites[0]?.id || "", name: "", jenis: "air_limbah", frekuensi_bulan: 6, tanggal_uji_terakhir: "", parameters: [emptyParam()] });
    setPointOpen(true);
  };

  const openEditPoint = (p) => {
    setEditing(p.id);
    setPForm({
      site_id: p.site_id, name: p.name, jenis: p.jenis, frekuensi_bulan: p.frekuensi_bulan,
      tanggal_uji_terakhir: p.tanggal_uji_terakhir || "",
      parameters: (p.parameters || []).map((x) => ({ nama: x.nama, satuan: x.satuan || "", baku_mutu: x.baku_mutu ?? "", baku_mutu_min: x.baku_mutu_min ?? "" })),
    });
    setPointOpen(true);
  };

  const savePoint = async () => {
    if (!pForm.site_id || !pForm.name) { toast.error("Lengkapi site & nama titik"); return; }
    const payload = {
      ...pForm,
      frekuensi_bulan: Number(pForm.frekuensi_bulan),
      tanggal_uji_terakhir: pForm.tanggal_uji_terakhir || null,
      parameters: pForm.parameters.filter((p) => p.nama).map((p) => ({
        nama: p.nama, satuan: p.satuan,
        baku_mutu: p.baku_mutu === "" ? null : Number(p.baku_mutu),
        baku_mutu_min: p.baku_mutu_min === "" ? null : Number(p.baku_mutu_min),
      })),
    };
    try {
      if (editing) await api.put(`/monitoring-points/${editing}`, payload);
      else await api.post("/monitoring-points", payload);
      toast.success(editing ? "Titik diperbarui" : "Titik penaatan ditambahkan");
      setPointOpen(false); load();
    } catch (e) { toast.error(apiError(e)); }
  };

  const delPoint = async (id) => {
    if (!window.confirm("Hapus titik penaatan ini?")) return;
    await api.delete(`/monitoring-points/${id}`); toast.success("Titik dihapus"); load();
  };

  const setParam = (i, field, val) => {
    const arr = [...pForm.parameters]; arr[i] = { ...arr[i], [field]: val }; setPForm({ ...pForm, parameters: arr });
  };

  return (
    <div className="animate-fade-up space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="font-head text-3xl font-bold text-emerald-950">Site & Titik Penaatan</h1>
          <p className="text-slate-500 mt-1">Atur lokasi dan titik uji (outlet IPAL, cerobong) beserta frekuensi wajib ujinya.</p>
        </div>
        <Dialog open={siteOpen} onOpenChange={setSiteOpen}>
          <DialogTrigger asChild>
            <Button data-testid="add-site-button" className="bg-[#064E3B] hover:bg-[#022C22] text-white">
              <Plus className="h-4 w-4 mr-1" /> Tambah Site
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-white">
            <DialogHeader><DialogTitle className="font-head text-emerald-950">Tambah Site / Lokasi</DialogTitle></DialogHeader>
            <div className="space-y-3">
              <div><Label>Nama Site</Label><Input data-testid="site-name-input" value={siteName} onChange={(e) => setSiteName(e.target.value)} placeholder="Pabrik Utama" className="mt-1" /></div>
              <div><Label>Alamat (opsional)</Label><Input data-testid="site-address-input" value={siteAddr} onChange={(e) => setSiteAddr(e.target.value)} className="mt-1" /></div>
            </div>
            <DialogFooter><Button data-testid="save-site-button" onClick={addSite} className="bg-[#064E3B] text-white">Simpan</Button></DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {sites.length === 0 && (
        <div className="bg-white border border-dashed border-slate-300 rounded-2xl p-10 text-center">
          <MapPin className="h-10 w-10 text-slate-300 mx-auto mb-3" />
          <p className="text-slate-500">Belum ada site. Tambahkan lokasi perusahaan Anda untuk mulai.</p>
        </div>
      )}

      <div className="space-y-5">
        {sites.map((s) => {
          const sp = points.filter((p) => p.site_id === s.id);
          return (
            <section key={s.id} className="bg-white rounded-2xl border border-slate-200 overflow-hidden" data-testid={`site-${s.id}`}>
              <div className="flex items-center justify-between px-5 py-4 bg-emerald-50/60 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <MapPin className="h-5 w-5 text-emerald-700" />
                  <div>
                    <div className="font-head font-semibold text-emerald-950">{s.name}</div>
                    {s.address && <div className="text-xs text-slate-500">{s.address}</div>}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button size="sm" variant="outline" data-testid={`add-point-${s.id}`} onClick={() => openNewPoint(s.id)}>
                    <Plus className="h-4 w-4 mr-1" /> Titik
                  </Button>
                  <button onClick={() => delSite(s.id)} data-testid={`delete-site-${s.id}`} className="h-8 w-8 grid place-items-center rounded-lg text-slate-400 hover:bg-red-50 hover:text-red-600">
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
              <div className="p-4 grid sm:grid-cols-2 gap-3">
                {sp.length === 0 && <p className="text-sm text-slate-400 p-2">Belum ada titik penaatan di site ini.</p>}
                {sp.map((p) => (
                  <div key={p.id} className={`rounded-xl border p-4 ${dueTone(p.days_until_due, !p.tanggal_uji_terakhir)}`} data-testid={`point-${p.id}`}>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        {p.jenis === "air_limbah" ? <Droplets className="h-5 w-5" /> : <Factory className="h-5 w-5" />}
                        <div>
                          <div className="font-semibold">{p.name}</div>
                          <div className="text-xs opacity-80">{JENIS_LABEL[p.jenis]} · {FREKUENSI_OPTIONS.find((f) => f.value === p.frekuensi_bulan)?.label.split(" ")[0]}</div>
                        </div>
                      </div>
                      <div className="flex gap-1">
                        <button onClick={() => openEditPoint(p)} data-testid={`edit-point-${p.id}`} className="h-7 w-7 grid place-items-center rounded-md hover:bg-black/5"><Pencil className="h-3.5 w-3.5" /></button>
                        <button onClick={() => delPoint(p.id)} data-testid={`delete-point-${p.id}`} className="h-7 w-7 grid place-items-center rounded-md hover:bg-black/5"><Trash2 className="h-3.5 w-3.5" /></button>
                      </div>
                    </div>
                    <div className="mt-3 flex items-center justify-between text-sm">
                      <span className="font-semibold">{!p.tanggal_uji_terakhir ? "Belum pernah diuji" : dueLabel(p.days_until_due)}</span>
                      <span className="text-xs opacity-70">{formatDate(p.tanggal_jatuh_tempo_berikutnya)}</span>
                    </div>
                    <div className="mt-2 text-xs opacity-70">{(p.parameters || []).length} parameter wajib uji</div>
                  </div>
                ))}
              </div>
            </section>
          );
        })}
      </div>

      <Dialog open={pointOpen} onOpenChange={setPointOpen}>
        <DialogContent className="bg-white max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader><DialogTitle className="font-head text-emerald-950">{editing ? "Edit Titik Penaatan" : "Tambah Titik Penaatan"}</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div className="grid sm:grid-cols-2 gap-3">
              <div>
                <Label>Site</Label>
                <Select value={pForm.site_id} onValueChange={(v) => setPForm({ ...pForm, site_id: v })}>
                  <SelectTrigger data-testid="point-site-select" className="mt-1"><SelectValue placeholder="Pilih site" /></SelectTrigger>
                  <SelectContent className="bg-white">{sites.map((s) => <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div>
                <Label>Nama Titik</Label>
                <Input data-testid="point-name-input" value={pForm.name} onChange={(e) => setPForm({ ...pForm, name: e.target.value })} placeholder="Outlet IPAL 1" className="mt-1" />
              </div>
              <div>
                <Label>Jenis</Label>
                <Select value={pForm.jenis} onValueChange={(v) => setPForm({ ...pForm, jenis: v })}>
                  <SelectTrigger data-testid="point-jenis-select" className="mt-1"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-white">{JENIS_OPTIONS.map((o) => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div>
                <Label>Frekuensi Wajib Uji</Label>
                <Select value={String(pForm.frekuensi_bulan)} onValueChange={(v) => setPForm({ ...pForm, frekuensi_bulan: Number(v) })}>
                  <SelectTrigger data-testid="point-freq-select" className="mt-1"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-white">{FREKUENSI_OPTIONS.map((o) => <SelectItem key={o.value} value={String(o.value)}>{o.label}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div className="sm:col-span-2">
                <Label>Tanggal Uji Terakhir (opsional — untuk hitung jatuh tempo)</Label>
                <Input data-testid="point-last-test-input" type="date" value={pForm.tanggal_uji_terakhir} onChange={(e) => setPForm({ ...pForm, tanggal_uji_terakhir: e.target.value })} className="mt-1" />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <Label>Parameter Wajib Uji & Baku Mutu</Label>
                <Button size="sm" variant="outline" data-testid="add-param-button" onClick={() => setPForm({ ...pForm, parameters: [...pForm.parameters, emptyParam()] })}>
                  <Plus className="h-3.5 w-3.5 mr-1" /> Parameter
                </Button>
              </div>
              <div className="space-y-2">
                {pForm.parameters.map((p, i) => (
                  <div key={i} className="grid grid-cols-12 gap-2 items-center" data-testid={`param-row-${i}`}>
                    <Input className="col-span-3" placeholder="pH / BOD" value={p.nama} onChange={(e) => setParam(i, "nama", e.target.value)} />
                    <Input className="col-span-2" placeholder="mg/L" value={p.satuan} onChange={(e) => setParam(i, "satuan", e.target.value)} />
                    <Input className="col-span-3" type="number" placeholder="Batas atas" value={p.baku_mutu} onChange={(e) => setParam(i, "baku_mutu", e.target.value)} />
                    <Input className="col-span-3" type="number" placeholder="Batas bawah (opsional)" value={p.baku_mutu_min} onChange={(e) => setParam(i, "baku_mutu_min", e.target.value)} />
                    <button className="col-span-1 grid place-items-center text-slate-400 hover:text-red-600" onClick={() => setPForm({ ...pForm, parameters: pForm.parameters.filter((_, idx) => idx !== i) })}><X className="h-4 w-4" /></button>
                  </div>
                ))}
              </div>
              <p className="text-xs text-slate-400 mt-2">Batas atas = nilai maksimum yang diizinkan baku mutu. Batas bawah dipakai untuk parameter seperti pH.</p>
            </div>
          </div>
          <DialogFooter><Button data-testid="save-point-button" onClick={savePoint} className="bg-[#064E3B] text-white">{editing ? "Simpan Perubahan" : "Simpan Titik"}</Button></DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
