import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import api, { API, apiError } from "@/lib/api";
import { JENIS_LABEL, formatDate } from "@/lib/helpers";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { FolderArchive, Upload, FileText, Trash2, Download, CheckCircle2, AlertTriangle, ExternalLink } from "lucide-react";

export default function Vault() {
  const [points, setPoints] = useState([]);
  const [labs, setLabs] = useState([]);
  const [selected, setSelected] = useState("");
  const [reports, setReports] = useState([]);
  const [open, setOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [form, setForm] = useState({ periode: "", tanggal_uji: "", lab_id: "", file: null });
  const [results, setResults] = useState([]);

  useEffect(() => {
    Promise.all([api.get("/monitoring-points"), api.get("/labs")]).then(([p, l]) => {
      setPoints(p.data); setLabs(l.data);
      if (p.data.length) setSelected(p.data[0].id);
    }).catch((e) => toast.error(apiError(e)));
  }, []);

  const point = useMemo(() => points.find((p) => p.id === selected), [points, selected]);

  const loadReports = async (id) => {
    if (!id) return;
    try {
      const { data } = await api.get(`/monitoring-points/${id}/lhu`);
      setReports(data);
    } catch (e) { toast.error(apiError(e)); }
  };
  useEffect(() => { loadReports(selected); }, [selected]);

  const openUpload = () => {
    setForm({ periode: "", tanggal_uji: "", lab_id: "", file: null });
    setResults((point?.parameters || []).map((p) => ({ nama: p.nama, satuan: p.satuan, baku_mutu: p.baku_mutu, baku_mutu_min: p.baku_mutu_min, nilai: "" })));
    setOpen(true);
  };

  const submit = async () => {
    if (!form.file || !form.periode || !form.tanggal_uji) { toast.error("Lengkapi file, periode, dan tanggal uji"); return; }
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("file", form.file);
      fd.append("periode", form.periode);
      fd.append("tanggal_uji", form.tanggal_uji);
      fd.append("lab_id", form.lab_id);
      fd.append("results", JSON.stringify(results.map((r) => ({ ...r, nilai: r.nilai === "" ? null : Number(r.nilai) }))));
      await api.post(`/monitoring-points/${selected}/lhu`, fd, { headers: { "Content-Type": "multipart/form-data" } });
      toast.success("LHU berhasil diunggah. Jadwal berikutnya dihitung ulang.");
      setOpen(false);
      await Promise.all([loadReports(selected), api.get("/monitoring-points").then(({ data }) => setPoints(data))]);
    } catch (e) { toast.error(apiError(e)); }
    finally { setUploading(false); }
  };

  const del = async (id) => {
    if (!window.confirm("Hapus LHU ini?")) return;
    await api.delete(`/lhu/${id}`); toast.success("LHU dihapus"); loadReports(selected);
  };

  const token = localStorage.getItem("swarna_token");
  const fileUrl = (path) => `${API}/files/${path}?token=${token}`;

  return (
    <div className="animate-fade-up space-y-6">
      <div>
        <h1 className="font-head text-3xl font-bold text-emerald-950">Vault LHU</h1>
        <p className="text-slate-500 mt-1">Simpan Laporan Hasil Uji per titik. Begitu diunggah, titik dianggap sudah diuji.</p>
      </div>

      {points.length === 0 ? (
        <div className="bg-white border border-dashed border-slate-300 rounded-2xl p-10 text-center">
          <FolderArchive className="h-10 w-10 text-slate-300 mx-auto mb-3" />
          <p className="text-slate-500">Belum ada titik penaatan. Buat dulu di menu Site & Titik Uji.</p>
        </div>
      ) : (
        <>
          <div className="flex items-end gap-3 flex-wrap">
            <div className="w-72">
              <Label>Pilih Titik Penaatan</Label>
              <Select value={selected} onValueChange={setSelected}>
                <SelectTrigger data-testid="vault-point-select" className="mt-1 bg-white"><SelectValue /></SelectTrigger>
                <SelectContent className="bg-white">
                  {points.map((p) => <SelectItem key={p.id} value={p.id}>{p.name} · {p.site_name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <Button data-testid="upload-lhu-button" onClick={openUpload} className="bg-[#064E3B] hover:bg-[#022C22] text-white">
              <Upload className="h-4 w-4 mr-1" /> Unggah LHU
            </Button>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 divide-y divide-slate-100" data-testid="lhu-list">
            {reports.length === 0 && <p className="text-sm text-slate-400 p-6 text-center">Belum ada LHU untuk titik ini.</p>}
            {reports.map((r) => {
              const melebihi = (r.results || []).filter((x) => x.status === "melebihi");
              return (
                <div key={r.id} className="p-4 flex items-start justify-between gap-4" data-testid={`lhu-${r.id}`}>
                  <div className="flex gap-3 min-w-0">
                    <div className="h-10 w-10 rounded-lg bg-emerald-50 grid place-items-center shrink-0"><FileText className="h-5 w-5 text-emerald-700" /></div>
                    <div className="min-w-0">
                      <div className="font-semibold text-emerald-950">{r.periode}</div>
                      <div className="text-xs text-slate-500">Uji: {formatDate(r.tanggal_uji)} {r.lab_name ? `· Lab: ${r.lab_name}` : ""}</div>
                      <div className="flex items-center gap-2 mt-2">
                        {melebihi.length === 0 ? (
                          <Badge className="bg-emerald-100 text-emerald-800 hover:bg-emerald-100"><CheckCircle2 className="h-3 w-3 mr-1" /> Semua sesuai baku mutu</Badge>
                        ) : (
                          <Badge className="bg-red-100 text-red-800 hover:bg-red-100"><AlertTriangle className="h-3 w-3 mr-1" /> {melebihi.length} parameter melebihi</Badge>
                        )}
                        <span className="text-xs text-slate-400">{(r.results || []).length} parameter</span>
                      </div>
                      {(r.results || []).length > 0 && (
                        <div className="flex flex-wrap gap-1.5 mt-2">
                          {r.results.map((x, i) => (
                            <span key={i} className={`text-[11px] px-2 py-0.5 rounded font-mono-data ${x.status === "melebihi" ? "bg-red-50 text-red-700" : "bg-slate-100 text-slate-600"}`}>
                              {x.nama}: {x.nilai ?? "-"}{x.satuan ? ` ${x.satuan}` : ""}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <a href={fileUrl(r.storage_path)} target="_blank" rel="noreferrer" data-testid={`view-lhu-${r.id}`} className="h-8 w-8 grid place-items-center rounded-lg text-slate-500 hover:bg-emerald-50 hover:text-emerald-700" title="Lihat dokumen"><ExternalLink className="h-4 w-4" /></a>
                    <a href={fileUrl(r.storage_path)} download={r.original_filename} className="h-8 w-8 grid place-items-center rounded-lg text-slate-500 hover:bg-emerald-50 hover:text-emerald-700" title="Unduh"><Download className="h-4 w-4" /></a>
                    <button onClick={() => del(r.id)} data-testid={`delete-lhu-${r.id}`} className="h-8 w-8 grid place-items-center rounded-lg text-slate-400 hover:bg-red-50 hover:text-red-600"><Trash2 className="h-4 w-4" /></button>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="bg-white max-w-xl max-h-[90vh] overflow-y-auto">
          <DialogHeader><DialogTitle className="font-head text-emerald-950">Unggah LHU — {point?.name}</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div className="grid sm:grid-cols-2 gap-3">
              <div><Label>Periode Pengujian</Label><Input data-testid="lhu-periode-input" value={form.periode} onChange={(e) => setForm({ ...form, periode: e.target.value })} placeholder="Semester 1 2026" className="mt-1" /></div>
              <div><Label>Tanggal Uji</Label><Input data-testid="lhu-date-input" type="date" value={form.tanggal_uji} onChange={(e) => setForm({ ...form, tanggal_uji: e.target.value })} className="mt-1" /></div>
            </div>
            <div>
              <Label>Laboratorium (opsional)</Label>
              <Select value={form.lab_id} onValueChange={(v) => setForm({ ...form, lab_id: v })}>
                <SelectTrigger data-testid="lhu-lab-select" className="mt-1"><SelectValue placeholder="Pilih lab" /></SelectTrigger>
                <SelectContent className="bg-white">{labs.map((l) => <SelectItem key={l.id} value={l.id}>{l.nama}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div>
              <Label>File LHU (PDF / Gambar)</Label>
              <Input data-testid="lhu-file-input" type="file" accept=".pdf,.png,.jpg,.jpeg,.webp" onChange={(e) => setForm({ ...form, file: e.target.files[0] })} className="mt-1" />
            </div>
            {results.length > 0 && (
              <div>
                <Label>Isi Hasil per Parameter</Label>
                <div className="space-y-2 mt-1">
                  {results.map((r, i) => (
                    <div key={i} className="grid grid-cols-12 gap-2 items-center">
                      <span className="col-span-4 text-sm text-slate-700">{r.nama} {r.satuan ? `(${r.satuan})` : ""}</span>
                      <Input className="col-span-4" type="number" placeholder="nilai" data-testid={`result-input-${i}`} value={r.nilai}
                        onChange={(e) => { const a = [...results]; a[i] = { ...a[i], nilai: e.target.value }; setResults(a); }} />
                      <span className="col-span-4 text-xs text-slate-400">Baku mutu: {r.baku_mutu_min != null ? `${r.baku_mutu_min} – ` : "≤ "}{r.baku_mutu ?? "-"}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
          <DialogFooter><Button data-testid="submit-lhu-button" onClick={submit} disabled={uploading} className="bg-[#064E3B] text-white">{uploading ? "Mengunggah…" : "Unggah & Hitung Ulang Jadwal"}</Button></DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
