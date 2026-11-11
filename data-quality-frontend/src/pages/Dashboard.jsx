import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, ArrowUpRight, CheckCircle2, Database, FileUp, Layers3, RefreshCw, ShieldAlert } from "lucide-react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip, Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts";
import { Link } from "react-router-dom";
import { getBatches } from "../api/batchApi";
import { Card, CardContent, CardHeader } from "../components/ui/Card";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import { sampleBatches, sampleStatuses, sampleTrend } from "../data/dashboardData";

const icons = [Layers3, CheckCircle2, ShieldAlert, AlertTriangle];
const fmt = (v) => Number.isFinite(Number(v)) ? Number(v).toLocaleString() : "—";
const statusOf = (b) => b.finalStatus || b.FINAL_STATUS || b.batchStatus || b.BATCH_STATUS || "UNKNOWN";
const idOf = (b) => b.batchId || b.batch_id || b.BATCH_ID || "—";
const scoreOf = (b) => b.overallScore ?? b.OVERALL_SCORE;

export default function Dashboard() {
  const [batches, setBatches] = useState([]);
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const load = async () => {
    setLoading(true); setError("");
    try {
      const data = await getBatches();
      const rows = Array.isArray(data) ? data : data?.batches || data?.data || [];
      setBatches(rows); setConnected(true);
    } catch (e) {
      setConnected(false); setError("Backend is not reachable. Start Spring Boot to load live batches.");
      setBatches([]);
    } finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);
  const counts = useMemo(() => {
    const all = batches;
    return {
      total: all.length,
      published: all.filter(b => ["PASS", "WARN"].includes(statusOf(b))).length,
      blocked: all.filter(b => ["BLOCK", "FAILED"].includes(statusOf(b))).length
    };
  }, [batches]);
  const metrics = [
    { label: "Total batches", value: connected ? fmt(counts.total) : "—", note: connected ? "Loaded from backend" : "Waiting for backend", Icon: icons[0] },
    { label: "Published batches", value: connected ? fmt(counts.published) : "—", note: "PASS and WARN", Icon: icons[1] },
    { label: "Blocked batches", value: connected ? fmt(counts.blocked) : "—", note: "BLOCK and FAILED", Icon: icons[2] },
    { label: "Backend status", value: connected ? "Connected" : "Offline", note: "Spring Boot API", Icon: icons[3] }
  ];
  const rows = batches.length ? batches.slice(0, 5) : sampleBatches;
  const statusData = connected ? [
    { name: "PASS", value: counts.published, color: "#16A34A" },
    { name: "BLOCK", value: counts.blocked, color: "#DC2626" }
  ].filter(x => x.value > 0) : sampleStatuses;
  return <div className="space-y-6">
    <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
      <div><p className="page-title">Good day, Sharan</p><p className="page-subtitle">Here’s what’s happening across your data quality pipeline.</p></div>
      <div className="flex gap-2"><Button variant="secondary" onClick={load} disabled={loading}><RefreshCw size={15} className={loading ? "animate-spin" : ""}/> Refresh</Button><Link to="/upload"><Button><FileUp size={16}/> Upload batch</Button></Link></div>
    </div>
    {error && <div className="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800"><AlertTriangle size={16}/>{error}</div>}
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {metrics.map(({label,value,note,Icon}) => <Card key={label}><CardContent className="flex items-start justify-between">
        <div><p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold tracking-tight text-slate-900">{value}</p><p className="mt-1 text-xs text-slate-400">{note}</p></div>
        <div className="rounded-lg bg-blue-50 p-2.5 text-electric"><Icon size={19}/></div>
      </CardContent></Card>)}
    </div>
    <div className="grid gap-5 xl:grid-cols-[1.6fr_1fr]">
      <Card>
        <CardHeader><div><h2 className="section-title">Quality score trend</h2><p className="mt-1 text-xs text-slate-400">Illustrative weekly trend</p></div><span className="rounded-md bg-slate-100 px-2 py-1 text-[11px] text-slate-500">Last 7 days</span></CardHeader>
        <CardContent><div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%"><AreaChart data={sampleTrend} margin={{top:10,right:8,left:-20,bottom:0}}>
            <defs><linearGradient id="scoreFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#3B82F6" stopOpacity={0.2}/><stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/></linearGradient></defs>
            <CartesianGrid stroke="#E2E8F0" strokeDasharray="3 3" vertical={false}/><XAxis dataKey="day" tickLine={false} axisLine={false} tick={{fontSize:11,fill:"#94A3B8"}}/><YAxis domain={[90,100]} tickLine={false} axisLine={false} tick={{fontSize:11,fill:"#94A3B8"}}/><Tooltip contentStyle={{borderRadius:10,border:"1px solid #E2E8F0",fontSize:12}}/><Area type="monotone" dataKey="score" stroke="#3B82F6" strokeWidth={2.5} fill="url(#scoreFill)" />
          </AreaChart></ResponsiveContainer>
        </div></CardContent>
      </Card>
      <Card>
        <CardHeader><div><h2 className="section-title">Batch outcomes</h2><p className="mt-1 text-xs text-slate-400">{connected ? "Current backend batches" : "Sample overview"}</p></div></CardHeader>
        <CardContent><div className="relative h-48">
          <ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={statusData} dataKey="value" nameKey="name" innerRadius={55} outerRadius={78} paddingAngle={3} stroke="none">{statusData.map((entry,i)=><Cell key={i} fill={entry.color}/>)}</Pie><Tooltip/></PieChart></ResponsiveContainer>
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center"><span className="text-2xl font-semibold text-slate-900">{connected ? counts.total : "128"}</span><span className="text-[11px] text-slate-400">Batches</span></div>
        </div><div className="mt-2 flex flex-wrap justify-center gap-x-4 gap-y-2">{statusData.map(s=><div key={s.name} className="flex items-center gap-1.5 text-xs text-slate-500"><span className="h-2 w-2 rounded-full" style={{background:s.color}}/>{s.name}<b className="text-slate-700">{s.value}</b></div>)}</div></CardContent>
      </Card>
    </div>
    <Card>
      <CardHeader><div><h2 className="section-title">Recent batches</h2><p className="mt-1 text-xs text-slate-400">Latest files submitted for validation</p></div><Link to="/batches" className="inline-flex items-center gap-1 text-xs font-semibold text-electric hover:text-blue-700">View all <ArrowUpRight size={14}/></Link></CardHeader>
      <div className="overflow-x-auto"><table className="w-full min-w-[650px] text-left text-sm"><thead className="bg-slate-50 text-[11px] uppercase tracking-wide text-slate-500"><tr><th className="px-5 py-3 font-medium">Batch</th><th className="px-5 py-3 font-medium">Records</th><th className="px-5 py-3 font-medium">DQ score</th><th className="px-5 py-3 font-medium">Status</th><th className="px-5 py-3 font-medium">Received</th></tr></thead><tbody className="divide-y divide-slate-100">{rows.map((b,i)=><tr key={idOf(b)+i} className="hover:bg-slate-50/70"><td className="px-5 py-3.5"><p className="font-medium text-slate-800">{idOf(b)}</p><p className="mt-0.5 text-xs text-slate-400">{b.fileName || b.FILE_NAME || "Transaction file"}</p></td><td className="px-5 py-3.5 text-slate-600">{fmt(b.recordCount ?? b.RECORD_COUNT)}</td><td className="px-5 py-3.5 font-medium text-slate-700">{scoreOf(b) == null ? "—" : `${Number(scoreOf(b)).toFixed(2)}%`}</td><td className="px-5 py-3.5"><Badge status={statusOf(b)}/></td><td className="px-5 py-3.5 text-xs text-slate-500">{b.receivedAt || b.RECEIVED_AT || "—"}</td></tr>)}</tbody></table></div>
      {!connected && <p className="border-t border-slate-100 px-5 py-3 text-xs text-slate-400">Sample rows are shown for layout preview only; they are not live backend data.</p>}
    </Card>
  </div>;
}
