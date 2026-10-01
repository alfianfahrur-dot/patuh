import { useEffect, useMemo, useState } from "react";
import api from "@/lib/api";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
  BarChart, Bar, Legend, Cell,
} from "recharts";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import {
  TrendingUp, TrendingDown, AlertTriangle, ShieldCheck, GitCompareArrows, Activity,
  CheckCircle2, XCircle, Minus, Clock,
} from "lucide-react";
import { formatDate } from "@/lib/helpers";

const COLOR = { green: "#059669", yellow: "#F59E0B", red: "#DC2626" };

function num(v) { const n = Number(v); return Number.isFinite(n) ? n : null; }

function getVal(report, paramName) {
  const r = (report?.results || []).find((x) => x.nama === paramName);
  return r ? num(r.nilai) : null;
}

function statusOf(val, bm, bmin) {
  if (val === null) return "nodata";
  if (bm != null && val > Number(bm)) return "melebihi";
  if (bmin != null && val < Number(bmin)) return "melebihi";
  return "sesuai";
}

export default function Analytics() {
  const [points, setPoints] = useState([]);
  const [compliance, setCompliance] = useState(null);
  const [pointId, setPointId] = useState("");
  const [reports, setReports] = useState([]);
  const [aId, setAId] = useState("");
  const [bId, setBId] = useState("");
  const [param, setParam] = useState("");
  const [trend, setTrend] = useState(null);

  useEffect(() => {
    api.get("/monitoring-points").then(({ data }) => {
      setPoints(data);
      if (data.length) setPointId(data[0].id);
    });
    api.get("/compliance").then(({ data }) => setCompliance(data));
  }, []);

  const point = useMemo(() => points.find((p) => p.id === pointId), [points, pointId]);
  const params = point?.parameters || [];

  useEffect(() => {
    if (!pointId) return;
    api.get(`/monitoring-points/${pointId}/lhu`).then(({ data }) => {
      const asc = [...data].reverse(); // lhu returns newest-first
      setReports(asc);
      if (asc.length >= 2) { setAId(asc[asc.length - 2].id); setBId(asc[asc.length - 1].id); }
      else if (asc.length === 1) { setAId(asc[0].id); setBId(asc[0].id); }
      else { setAId(""); setBId(""); }
    });
    if (params.length) setParam(params[0].nama); else setParam("");
  }, [pointId]);

  useEffect(() => {
    if (pointId && param) {
      api.get(`/monitoring-points/${pointId}/trend`, { params: { parameter: param } }).then(({ data }) => setTrend(data));
    } else setTrend(null);
  }, [pointId, param]);

  const repA = reports.find((r) => r.id === aId);
  const repB = reports.find((r) => r.id === bId);

  const comparison = useMemo(() => {
    if (!repA || !repB) return [];
    return params.map((p) => {
      const a = getVal(repA, p.nama);
      const b = getVal(repB, p.nama);
      let delta = null;
      if (a != null && b != null && a !== 0) delta = Math.round(((b - a) / Math.abs(a)) * 1000) / 10;
      return { nama: p.nama, satuan: p.satuan || "", baku_mutu: p.baku_mutu, baku_mutu_min: p.baku_mutu_min,
        a, b, delta, statusB: statusOf(b, p.baku_mutu, p.baku_mutu_min) };
    });
  }, [repA, repB, params]);

  const barData = comparison.filter((c) => c.a != null || c.b != null)
    .map((c) => ({ name: c.nama, a: c.a, b: c.b }));

  const chartData = (trend?.series || []).map((s) => ({ name: s.periode, nilai: s.nilai, status: s.status }));

  const worse = comparison.filter((c) => c.delta != null && c.delta > 0 && c.baku_mutu != null).length;
  const better = comparison.filter((c) => c.delta != null && c.delta < 0 && c.baku_mutu != null).length;

  return (
    <div className="animate-fade-up space-y-6">
      <div>
        <h1 className="font-head text-3xl font-bold text-emerald-950">Skor Ketaatan & Analitik</h1>
        <p className="text-slate-500 mt-1">Bandingkan antar periode uji dan pantau pergerakan tiap parameter.</p>
      </div>

      {/* SCORE STRIP */}
      {compliance && (
        <div className="grid sm:grid-cols-4 gap-4">
          <div className="rounded-2xl p-5 text-white relative overflow-hidden" style={{ background: COLOR[compliance.color] }} data-testid="score-card">
            <div className="absolute -right-6 -bottom-6 h-24 w-24 rounded-full bg-white/10" />
            <ShieldCheck className="h-6 w-6 opacity-80" />
            <div className="text-4xl font-head font-bold mt-2">{compliance.percent}%</div>
            <div className="text-sm opacity-90">Skor Ketaatan</div>
          </div>
          <div className="rounded-2xl p-5 bg-white border border-slate-200">
            <CheckCircle2 className="h-5 w-5 text-emerald-600" />
            <div className="text-3xl font-head font-bold text-emerald-700 mt-2">{compliance.taat}</div>
            <div className="text-sm text-slate-500">Titik Taat</div>
          </div>
          <div className="rounded-2xl p-5 bg-white border border-slate-200">
            <AlertTriangle className="h-5 w-5 text-red-500" />
            <div className="text-3xl font-head font-bold text-red-600 mt-2">{compliance.total - compliance.taat}</div>
            <div className="text-sm text-slate-500">Perlu Perhatian</div>
          </div>
          <div className="rounded-2xl p-5 bg-white border border-slate-200">
            <Activity className="h-5 w-5 text-emerald-500" />
            <div className="text-3xl font-head font-bold text-emerald-950 mt-2">{compliance.total}</div>
            <div className="text-sm text-slate-500">Total Titik</div>
          </div>
        </div>
      )}

      {/* POINT PICKER */}
      {points.length === 0 ? (
        <div className="bg-white rounded-2xl border border-dashed border-slate-300 p-10 text-center text-slate-400">
          Belum ada titik penaatan untuk dianalisis.
        </div>
      ) : (
        <>
          <div className="w-80">
            <Label>Pilih Titik Penaatan</Label>
            <Select value={pointId} onValueChange={setPointId}>
              <SelectTrigger data-testid="analytics-point-select" className="mt-1 bg-white"><SelectValue /></SelectTrigger>
              <SelectContent className="bg-white">
                {points.map((p) => <SelectItem key={p.id} value={p.id}>{p.name} · {p.site_name}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>

          {/* PERIOD COMPARISON */}
          <section className="bg-white rounded-2xl border border-slate-200 p-5" data-testid="comparison-section">
            <div className="flex items-center gap-2 mb-1">
              <GitCompareArrows className="h-5 w-5 text-emerald-700" />
              <h2 className="font-head text-lg font-semibold text-emerald-950">Bandingkan Antar Periode</h2>
            </div>
            <p className="text-sm text-slate-500 mb-4">Pilih dua periode pengujian untuk melihat perubahan tiap parameter.</p>

            {reports.length < 2 ? (
              <div className="py-12 text-center text-slate-400 text-sm" data-testid="comparison-empty">
                Butuh minimal 2 periode pengujian. Unggah LHU lagi di Vault untuk mulai membandingkan.
              </div>
            ) : (
              <>
                <div className="flex flex-wrap items-end gap-3 mb-5">
                  <div className="w-52">
                    <Label className="text-xs text-slate-500">Periode A (awal)</Label>
                    <Select value={aId} onValueChange={setAId}>
                      <SelectTrigger data-testid="period-a-select" className="mt-1"><SelectValue /></SelectTrigger>
                      <SelectContent className="bg-white">
                        {reports.map((r) => <SelectItem key={r.id} value={r.id}>{r.periode}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="h-10 grid place-items-center text-slate-400 font-head">vs</div>
                  <div className="w-52">
                    <Label className="text-xs text-slate-500">Periode B (akhir)</Label>
                    <Select value={bId} onValueChange={setBId}>
                      <SelectTrigger data-testid="period-b-select" className="mt-1"><SelectValue /></SelectTrigger>
                      <SelectContent className="bg-white">
                        {reports.map((r) => <SelectItem key={r.id} value={r.id}>{r.periode}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex gap-2 ml-auto">
                    {better > 0 && <Badge className="bg-emerald-100 text-emerald-800 hover:bg-emerald-100"><TrendingDown className="h-3 w-3 mr-1" /> {better} membaik</Badge>}
                    {worse > 0 && <Badge className="bg-red-100 text-red-800 hover:bg-red-100"><TrendingUp className="h-3 w-3 mr-1" /> {worse} memburuk</Badge>}
                  </div>
                </div>

                {barData.length > 0 && (
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart data={barData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }} barGap={6}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
                      <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#64748B" }} />
                      <YAxis tick={{ fontSize: 12, fill: "#64748B" }} />
                      <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #E2E8F0", fontSize: 13 }} cursor={{ fill: "#F1F5F9" }} />
                      <Legend wrapperStyle={{ fontSize: 13 }} />
                      <Bar dataKey="a" name={repA?.periode || "Periode A"} fill="#A7F3D0" radius={[6, 6, 0, 0]} />
                      <Bar dataKey="b" name={repB?.periode || "Periode B"} fill="#064E3B" radius={[6, 6, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                )}

                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 mt-5">
                  {comparison.map((c) => {
                    const dirWorse = c.delta != null && c.delta > 0; // toward max baku mutu
                    return (
                      <div key={c.nama} className="rounded-xl border border-slate-200 p-4" data-testid={`compare-${c.nama}`}>
                        <div className="flex items-center justify-between">
                          <span className="font-head font-semibold text-emerald-950">{c.nama}</span>
                          {c.statusB === "melebihi" ? (
                            <Badge className="bg-red-100 text-red-800 hover:bg-red-100"><XCircle className="h-3 w-3 mr-1" /> Melebihi</Badge>
                          ) : c.statusB === "sesuai" ? (
                            <Badge className="bg-emerald-100 text-emerald-800 hover:bg-emerald-100"><CheckCircle2 className="h-3 w-3 mr-1" /> Sesuai</Badge>
                          ) : <Badge variant="outline" className="text-slate-400">—</Badge>}
                        </div>
                        <div className="flex items-end gap-2 mt-3">
                          <div className="text-slate-400 font-mono-data text-sm">{c.a ?? "-"}</div>
                          <Minus className="h-3 w-3 text-slate-300 mb-1 rotate-90 sm:rotate-0" />
                          <div className="text-2xl font-head font-bold text-emerald-950 font-mono-data">{c.b ?? "-"}</div>
                          <span className="text-xs text-slate-400 mb-1">{c.satuan}</span>
                        </div>
                        <div className="flex items-center justify-between mt-2">
                          {c.delta == null ? (
                            <span className="text-xs text-slate-400">Tidak ada pembanding</span>
                          ) : (
                            <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded ${dirWorse ? "bg-red-50 text-red-700" : c.delta < 0 ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-600"}`}>
                              {c.delta > 0 ? <>▲ +{c.delta}%</> : c.delta < 0 ? <>▼ {c.delta}%</> : <>0%</>}
                            </span>
                          )}
                          {c.baku_mutu != null && <span className="text-[11px] text-slate-400">Baku mutu ≤ {c.baku_mutu}</span>}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </>
            )}
          </section>

          {/* TREND */}
          <section className="bg-white rounded-2xl border border-slate-200 p-5" data-testid="trend-section">
            <div className="flex items-center gap-2 mb-4">
              <Activity className="h-5 w-5 text-emerald-700" />
              <h2 className="font-head text-lg font-semibold text-emerald-950">Tren per Parameter</h2>
            </div>
            <div className="w-56 mb-5">
              <Label>Parameter</Label>
              <Select value={param} onValueChange={setParam} disabled={!params.length}>
                <SelectTrigger data-testid="trend-param-select" className="mt-1"><SelectValue placeholder="Pilih parameter" /></SelectTrigger>
                <SelectContent className="bg-white">{params.map((p) => <SelectItem key={p.nama} value={p.nama}>{p.nama}</SelectItem>)}</SelectContent>
              </Select>
            </div>

            {!trend || chartData.length === 0 ? (
              <div className="py-16 text-center text-slate-400 text-sm" data-testid="trend-empty">
                Belum ada cukup data uji untuk menampilkan tren. Unggah LHU dengan nilai parameter di Vault.
              </div>
            ) : (
              <div data-testid="trend-chart">
                <div className="flex items-center gap-3 mb-3 flex-wrap">
                  {trend.change_percent != null && (
                    <span className={`inline-flex items-center gap-1 text-sm font-semibold px-2.5 py-1 rounded-lg ${trend.change_percent > 0 ? "bg-red-50 text-red-700" : "bg-emerald-50 text-emerald-700"}`} data-testid="trend-change-badge">
                      {trend.change_percent > 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                      {trend.change_percent > 0 ? "▲" : "▼"} {Math.abs(trend.change_percent)}% vs periode lalu
                    </span>
                  )}
                  {trend.perlu_perhatian && (
                    <span className="inline-flex items-center gap-1 text-sm font-semibold px-2.5 py-1 rounded-lg bg-amber-50 text-amber-700" data-testid="trend-warning-badge">
                      <AlertTriangle className="h-4 w-4" /> Perlu Perhatian
                    </span>
                  )}
                  {trend.baku_mutu != null && <span className="text-xs text-slate-500">Baku mutu: ≤ {trend.baku_mutu} {trend.satuan}</span>}
                </div>
                <ResponsiveContainer width="100%" height={320}>
                  <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                    <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#64748B" }} />
                    <YAxis tick={{ fontSize: 12, fill: "#64748B" }} />
                    <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #E2E8F0", fontSize: 13 }} />
                    {trend.baku_mutu != null && (
                      <ReferenceLine y={trend.baku_mutu} stroke="#DC2626" strokeDasharray="6 4" label={{ value: "Baku Mutu", fill: "#DC2626", fontSize: 11, position: "right" }} />
                    )}
                    {trend.baku_mutu_min != null && (
                      <ReferenceLine y={trend.baku_mutu_min} stroke="#F59E0B" strokeDasharray="6 4" label={{ value: "Batas bawah", fill: "#F59E0B", fontSize: 11, position: "right" }} />
                    )}
                    <Line type="monotone" dataKey="nilai" stroke="#064E3B" strokeWidth={2.5}
                      dot={(props) => {
                        const { cx, cy, payload } = props;
                        const danger = payload.status === "melebihi";
                        return <circle key={`${cx}-${cy}`} cx={cx} cy={cy} r={5} fill={danger ? "#DC2626" : "#059669"} stroke="#fff" strokeWidth={2} />;
                      }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </section>

          {/* PER-POINT BREAKDOWN */}
          {compliance?.detail?.length > 0 && (
            <section className="bg-white rounded-2xl border border-slate-200 overflow-hidden" data-testid="breakdown-section">
              <div className="px-5 py-4 border-b border-slate-100">
                <h2 className="font-head text-lg font-semibold text-emerald-950">Rincian Ketaatan per Titik</h2>
              </div>
              <div className="divide-y divide-slate-100">
                {compliance.detail.map((d) => (
                  <div key={d.id} className="px-5 py-3 flex items-center justify-between gap-3" data-testid={`breakdown-${d.id}`}>
                    <span className="font-medium text-emerald-950 truncate">{d.name}</span>
                    <div className="flex items-center gap-2 shrink-0">
                      <Badge className={d.on_time ? "bg-emerald-100 text-emerald-800 hover:bg-emerald-100" : "bg-red-100 text-red-800 hover:bg-red-100"}>
                        <Clock className="h-3 w-3 mr-1" /> {d.on_time ? "Tepat waktu" : "Telat / belum uji"}
                      </Badge>
                      <Badge className={d.hasil_sesuai ? "bg-emerald-100 text-emerald-800 hover:bg-emerald-100" : "bg-amber-100 text-amber-800 hover:bg-amber-100"}>
                        {d.hasil_sesuai ? <CheckCircle2 className="h-3 w-3 mr-1" /> : <AlertTriangle className="h-3 w-3 mr-1" />}
                        {d.hasil_sesuai ? "Hasil sesuai" : "Ada yang melebihi"}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
