import { useEffect, useState } from "react";
import { Search, RefreshCw, Database } from "lucide-react";
import { getBatches } from "../api/batchApi";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import { Card } from "../components/ui/Card";
import { Link } from "react-router-dom";

export default function Batches() {
  const [rows,setRows]=useState([]); const [query,setQuery]=useState(""); const [loading,setLoading]=useState(true); const [error,setError]=useState("");
  const load=async()=>{setLoading(true);setError("");try{const d=await getBatches();setRows(Array.isArray(d)?d:d?.batches||d?.data||[]);}catch(e){setError("Could not load batches. Check that Spring Boot is running on port 8080.");}finally{setLoading(false);}};
  useEffect(()=>{load();},[]);
  const filtered=rows.filter(b=>JSON.stringify(b).toLowerCase().includes(query.toLowerCase()));
  const get=(b,...keys)=>keys.map(k=>b[k]).find(v=>v!==undefined&&v!==null) ?? "—";
  return <div className="space-y-5">
    <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end"><div><h1 className="page-title">Batches</h1><p className="page-subtitle">Browse uploaded transaction batches and their processing status.</p></div><Button variant="secondary" onClick={load} disabled={loading}><RefreshCw size={15}/> Refresh</Button></div>
    {error&&<p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
    <Card><div className="flex flex-col gap-3 border-b border-slate-100 p-4 sm:flex-row sm:items-center sm:justify-between"><div className="relative w-full sm:max-w-sm"><Search size={16} className="absolute left-3 top-3 text-slate-400"/><Input className="pl-9" placeholder="Search batch ID or file name..." value={query} onChange={e=>setQuery(e.target.value)}/></div><span className="text-xs text-slate-400">{filtered.length} batches</span></div>
    {loading?<p className="p-8 text-center text-sm text-slate-500">Loading batches…</p>:filtered.length===0?<div className="p-12 text-center"><Database className="mx-auto text-slate-300" size={28}/><p className="mt-3 text-sm font-medium text-slate-700">No batches found</p><p className="mt-1 text-xs text-slate-400">Upload a CSV file to get started.</p><Link to="/upload" className="mt-4 inline-block text-sm font-semibold text-electric">Upload a batch</Link></div>:
    <div className="overflow-x-auto"><table className="w-full min-w-[680px] text-left text-sm"><thead className="bg-slate-50 text-[11px] uppercase tracking-wide text-slate-500"><tr>{["Batch ID","File name","Records","Status","Received"].map(x=><th key={x} className="px-5 py-3 font-medium">{x}</th>)}</tr></thead><tbody className="divide-y divide-slate-100">{filtered.map((b,i)=><tr key={get(b,"batchId","BATCH_ID")+i} className="hover:bg-slate-50"><td className="px-5 py-4 font-medium text-navy">{get(b,"batchId","batch_id","BATCH_ID")}</td><td className="px-5 py-4 text-slate-600">{get(b,"fileName","FILE_NAME")}</td><td className="px-5 py-4 text-slate-600">{get(b,"recordCount","RECORD_COUNT")}</td><td className="px-5 py-4"><Badge status={get(b,"batchStatus","BATCH_STATUS","finalStatus","FINAL_STATUS")}/></td><td className="px-5 py-4 text-xs text-slate-500">{get(b,"receivedAt","RECEIVED_AT")}</td></tr>)}</tbody></table></div>}
    </Card>
  </div>;
}
