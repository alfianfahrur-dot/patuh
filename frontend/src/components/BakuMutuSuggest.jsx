import { useState } from "react";
import { toast } from "sonner";
import api, { apiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Sparkles, Search, ShieldCheck, AlertTriangle, CheckCircle2, ChevronDown, ChevronUp } from "lucide-react";

const regBadge = (status) => {
  if (status === "berlaku") return "bg-emerald-100 text-emerald-800";
  if (status === "berlaku_sebagian") return "bg-amber-100 text-amber-800";
  if (status === "dicabut") return "bg-red-100 text-red-800";
  return "bg-slate-100 text-slate-700";
};

const batasText = (p) => {
  if (p.tipe === "rentang") return `${p.min ?? "-"} – ${p.maks ?? "-"}`;
  if (p.tipe === "negatif") return p.teks || "Negatif";
  return p.maks ?? "-";
};

export default function BakuMutuSuggest({ kategori, onApply }) {
  const [q, setQ] = useState("");
  const [debit, setDebit] = useState("");
  const [bahanBakar, setBahanBakar] = useState("");
  const [kapasitasKw, setKapasitasKw] = useState("");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState([]);
  const [searched, setSearched] = useState(false);
  const [expanded, setExpanded] = useState(null);

  const isEmisi = kategori === "emisi";

  const search = async () => {
    setLoading(true);
    try {
      const params = { kategori };
      if (q) params.q = q;
      if (debit !== "") params.debit = Number(debit);
      if (bahanBakar) params.bahan_bakar = bahanBakar;
      if (kapasitasKw !== "") params.kapasitas_kw = Number(kapasitasKw);
      const { data } = await api.get("/baku-mutu/saran", { params });
      setData(data.hasil || []);
      setSearched(true);
    } catch (e) { toast.error(apiError(e)); }
    finally { setLoading(false); }
  };

  return (
    <div className="rounded-xl border border-emerald-200 bg-emerald-50/40 p-4" data-testid="bakumutu-suggest">
      <div className="flex items-center gap-2 mb-3">
        <Sparkles className="h-4 w-4 text-emerald-700" />
        <h3 className="font-head font-semibold text-emerald-950 text-sm">Saran Baku Mutu Otomatis</h3>
      </div>

      <div className="grid sm:grid-cols-2 gap-2">
        <div className="sm:col-span-2">
          <Label className="text-xs">Jenis kegiatan / sumber</Label>
          <Input
            data-testid="suggest-q-input"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), search())}
            placeholder={isEmisi ? "mis. genset, boiler batubara" : "mis. hotel, rumah sakit, tekstil, sawit"}
            className="mt-1 bg-white"
          />
        </div>
        {!isEmisi && (
          <div>
            <Label className="text-xs">Debit air limbah (m³/hari, opsional)</Label>
            <Input data-testid="suggest-debit-input" type="number" value={debit} onChange={(e) => setDebit(e.target.value)} placeholder="mis. 120" className="mt-1 bg-white" />
          </div>
        )}
        {isEmisi && (
          <>
            <div>
              <Label className="text-xs">Bahan bakar (opsional)</Label>
              <Select value={bahanBakar || "none"} onValueChange={(v) => setBahanBakar(v === "none" ? "" : v)}>
                <SelectTrigger data-testid="suggest-fuel-select" className="mt-1 bg-white"><SelectValue placeholder="Pilih" /></SelectTrigger>
                <SelectContent className="bg-white">
                  <SelectItem value="none">—</SelectItem>
                  <SelectItem value="minyak">Minyak / cair (solar)</SelectItem>
                  <SelectItem value="gas">Gas</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-xs">Kapasitas (kW, opsional)</Label>
              <Input data-testid="suggest-kw-input" type="number" value={kapasitasKw} onChange={(e) => setKapasitasKw(e.target.value)} placeholder="mis. 500" className="mt-1 bg-white" />
            </div>
          </>
        )}
      </div>

      <Button type="button" size="sm" onClick={search} disabled={loading} data-testid="suggest-search-button" className="mt-3 bg-[#064E3B] hover:bg-[#022C22] text-white">
        <Search className="h-4 w-4 mr-1" /> {loading ? "Mencari…" : "Cari Saran"}
      </Button>

      {searched && data.length === 0 && (
        <p className="text-sm text-slate-500 mt-3" data-testid="suggest-empty">Tidak ada saran yang cocok. Coba kata kunci lain atau isi parameter secara manual di bawah.</p>
      )}

      <div className="space-y-3 mt-3">
        {data.map((s) => (
          <div key={s.id} className="bg-white rounded-xl border border-slate-200 p-4" data-testid={`suggest-card-${s.id}`}>
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <div className="font-semibold text-emerald-950 text-sm">{s.sektor}</div>
                <div className="text-xs text-slate-500">{s.sub_kategori}</div>
              </div>
              <Badge className={`${regBadge(s.regulasi?.status)} shrink-0 text-[10px]`}>{s.regulasi?.status || "-"}</Badge>
            </div>
            <div className="text-[11px] text-slate-400 mt-1">{s.regulasi?.judul}</div>

            {s.regulasi_dicabut && (
              <div className="mt-2 flex items-start gap-2 bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-xs text-red-800" data-testid={`suggest-revoked-${s.id}`}>
                <AlertTriangle className="h-3.5 w-3.5 mt-0.5 shrink-0" /> Regulasi ini sudah dicabut — jangan dipakai untuk pelaporan baru.
              </div>
            )}
            {s.perlu_verifikasi && (
              <div className="mt-2 flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 text-xs text-amber-800" data-testid={`suggest-verify-${s.id}`}>
                <AlertTriangle className="h-3.5 w-3.5 mt-0.5 shrink-0" /> Angka ini perlu dicek ke naskah resmi sebelum dipakai untuk pelaporan.
              </div>
            )}

            {s.kondisi_penerapan && <div className="text-xs text-slate-600 mt-2"><span className="font-medium">Kondisi:</span> {s.kondisi_penerapan}</div>}

            {s.alasan_cocok?.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {s.alasan_cocok.slice(0, 3).map((a, i) => (
                  <span key={i} className="inline-flex items-center gap-1 text-[10px] bg-emerald-50 text-emerald-700 rounded-full px-2 py-0.5">
                    <CheckCircle2 className="h-3 w-3" /> {a}
                  </span>
                ))}
              </div>
            )}

            <button type="button" onClick={() => setExpanded(expanded === s.id ? null : s.id)} className="mt-2 text-xs text-emerald-700 font-medium inline-flex items-center gap-1">
              {expanded === s.id ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
              {(s.parameter || []).length} parameter
            </button>

            {expanded === s.id && (
              <div className="mt-2 border border-slate-100 rounded-lg overflow-hidden">
                <table className="w-full text-xs">
                  <thead className="bg-slate-50 text-slate-500">
                    <tr><th className="text-left px-3 py-1.5">Parameter</th><th className="text-left px-3 py-1.5">Batas</th><th className="text-left px-3 py-1.5">Satuan</th></tr>
                  </thead>
                  <tbody>
                    {(s.parameter || []).map((p, i) => (
                      <tr key={i} className="border-t border-slate-100">
                        <td className="px-3 py-1.5 text-slate-700">{p.nama}</td>
                        <td className="px-3 py-1.5 text-slate-700">{batasText(p)}</td>
                        <td className="px-3 py-1.5 text-slate-500">{p.satuan || "-"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {(s.kuantitas_air_limbah_maks || []).length > 0 && (
                  <div className="px-3 py-2 text-[11px] text-slate-500 bg-slate-50 border-t border-slate-100">
                    Kuantitas maks: {s.kuantitas_air_limbah_maks.map((k) => `${k.nilai} ${k.satuan} (${k.label})`).join("; ")}
                  </div>
                )}
              </div>
            )}

            <Button type="button" size="sm" data-testid={`suggest-apply-${s.id}`} onClick={() => { onApply(s); toast.success("Baku mutu diterapkan ke parameter. Silakan periksa / edit di bawah."); }} className="mt-3 bg-emerald-600 hover:bg-emerald-700 text-white">
              <ShieldCheck className="h-4 w-4 mr-1" /> Terapkan
            </Button>
          </div>
        ))}
      </div>

      <p className="text-[11px] text-slate-400 mt-3 border-t border-emerald-100 pt-2">
        Saran otomatis bersifat acuan. Baku mutu daerah, Persetujuan Teknis, dan dokumen lingkungan perusahaan dapat lebih ketat dan harus didahulukan.
      </p>
    </div>
  );
}
