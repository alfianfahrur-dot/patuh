import { useEffect, useMemo, useState } from "react";
import api from "@/lib/api";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
} from "recharts";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { TrendingUp, TrendingDown, AlertTriangle, ShieldCheck } from "lucide-react";

const COLOR = { green: "#059669", yellow: "#F59E0B", red: "#DC2626" };

export default function Analytics() {
  const [points, setPoints] = useState([]);
  const [compliance, setCompliance] = useState(null);
  const [pointId, setPointId] = useState("");
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
    if (params.length) setParam(params[0].nama);
    else setParam("");
  }, [pointId]);

  useEffect(() => {
    if (pointId && param) {
      api.get(`/monitoring-points/${pointId}/trend`, { params: { parameter: param } }).then(({ data }) => setTrend(data));
    } else setTrend(null);
  }, [pointId, param]);

  const chartData = (trend?.series || []).map((s) => ({ name: s.periode, nilai: s.nilai, status: s.status }));

  return (
    <div className="animate-fade-up space-y-6">
      <div>
        <h1 className="font-head text-3xl font-bold text-emerald-950">Skor Ketaatan & Tren</h1>
        <p className="text-slate-500 mt-1">Lihat ringkasan kepatuhan dan pergerakan nilai parameter antar periode.</p>
      </div>

      {compliance && (
        <div className="grid sm:grid-cols-4 gap-4">
          <div className="rounded-2xl p-5 text-white" style={{ background: COLOR[compliance.color] }} data-testid="score-card">
            <ShieldCheck className="h-6 w-6 opacity-80" />
            <div className="text-4xl font-head font-bold mt-2">{compliance.percent}%</div>
            <div className="text-sm opacity-90">Skor Ketaatan</div>
          </div>
          <div className="rounded-2xl p-5 bg-white border border-slate-200">
            <div className="text-3xl font-head font-bold text-emerald-700">{compliance.taat}</div>
            <div className="text-sm text-slate-500">Titik Taat</div>
          </div>
          <div className="rounded-2xl p-5 bg-white border border-slate-200">
            <div className="text-3xl font-head font-bold text-red-600">{compliance.total - compliance.taat}</div>
            <div className="text-sm text-slate-500">Perlu Perhatian</div>
          </div>
          <div className="rounded-2xl p-5 bg-white border border-slate-200">
            <div className="text-3xl font-head font-bold text-emerald-950">{compliance.total}</div>
            <div className="text-sm text-slate-500">Total Titik</div>
          </div>
        </div>
      )}

      <div className="bg-white rounded-2xl border border-slate-200 p-5">
        <h2 className="font-head text-lg font-semibold text-emerald-950 mb-4">Tren per Parameter</h2>
        <div className="flex gap-3 flex-wrap mb-5">
          <div className="w-64">
            <Label>Titik Penaatan</Label>
            <Select value={pointId} onValueChange={setPointId}>
              <SelectTrigger data-testid="trend-point-select" className="mt-1"><SelectValue placeholder="Pilih titik" /></SelectTrigger>
              <SelectContent className="bg-white">{points.map((p) => <SelectItem key={p.id} value={p.id}>{p.name} · {p.site_name}</SelectItem>)}</SelectContent>
            </Select>
          </div>
          <div className="w-48">
            <Label>Parameter</Label>
            <Select value={param} onValueChange={setParam} disabled={!params.length}>
              <SelectTrigger data-testid="trend-param-select" className="mt-1"><SelectValue placeholder="Pilih parameter" /></SelectTrigger>
              <SelectContent className="bg-white">{params.map((p) => <SelectItem key={p.nama} value={p.nama}>{p.nama}</SelectItem>)}</SelectContent>
            </Select>
          </div>
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
      </div>
    </div>
  );
}
