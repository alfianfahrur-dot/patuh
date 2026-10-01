import { useEffect, useState } from "react";
import api from "@/lib/api";
import { formatDate } from "@/lib/helpers";
import { Badge } from "@/components/ui/badge";
import { Bell, Mail, MessageCircle, CheckCircle2, XCircle } from "lucide-react";

export default function Notifications() {
  const [logs, setLogs] = useState([]);
  useEffect(() => { api.get("/notifications").then(({ data }) => setLogs(data)); }, []);

  return (
    <div className="animate-fade-up space-y-6">
      <div>
        <h1 className="font-head text-3xl font-bold text-emerald-950">Log Pengingat</h1>
        <p className="text-slate-500 mt-1">Catatan setiap pengingat yang dikirim — untuk audit dan pelacakan.</p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden" data-testid="notification-log">
        {logs.length === 0 ? (
          <div className="p-10 text-center text-slate-400"><Bell className="h-10 w-10 mx-auto mb-3 text-slate-300" />Belum ada pengingat terkirim.</div>
        ) : (
          <div className="divide-y divide-slate-100">
            {logs.map((l) => (
              <div key={l.id} className="px-5 py-3 flex items-center justify-between gap-3" data-testid={`notif-${l.id}`}>
                <div className="flex items-center gap-3 min-w-0">
                  <div className={`h-9 w-9 rounded-lg grid place-items-center shrink-0 ${l.channel === "whatsapp" ? "bg-green-50 text-green-600" : "bg-emerald-50 text-emerald-700"}`}>
                    {l.channel === "whatsapp" ? <MessageCircle className="h-4 w-4" /> : <Mail className="h-4 w-4" />}
                  </div>
                  <div className="min-w-0">
                    <div className="font-medium text-emerald-950 truncate">{l.monitoring_point_name || l.message}</div>
                    <div className="text-xs text-slate-500 truncate">Ke: {l.recipient_email} · {formatDate(l.sent_at)}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {l.type && <Badge variant="outline" className="text-xs">{l.type}</Badge>}
                  {l.status === "terkirim"
                    ? <Badge className="bg-emerald-100 text-emerald-800 hover:bg-emerald-100"><CheckCircle2 className="h-3 w-3 mr-1" /> Terkirim</Badge>
                    : <Badge className="bg-red-100 text-red-800 hover:bg-red-100"><XCircle className="h-3 w-3 mr-1" /> Gagal</Badge>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
