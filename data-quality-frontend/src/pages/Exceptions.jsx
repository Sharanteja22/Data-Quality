import { useEffect, useState } from "react";
import { AlertCircle, RefreshCw, Search } from "lucide-react";
import { getBatches } from "../api/batchApi";
import { getRunExceptions } from "../api/runApi";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import { Card } from "../components/ui/Card";

export default function Exceptions() {
  const [rows,setRows]=useState([]); const [query,setQuery]=useState(""); const [loading,setLoading]=useState(true); const [error,setError]=useState("");
  const load=async()=>{setLoading(true);setError("");try{const data=await getBatches();const batches=Array.isArray(data)?data:data?.batches||data?.data||[];const all=[];for(const b of batches){const batchId=b.batchId||b.BATCH_ID;try{const details=await (await import("../api/batchApi")).getBatch(batchId);const runs=details?.runs||details?.batchRuns||[];for(const r of runs){const runId=r.runId||r.RUN_ID;if(runId){const ex=await getRunExceptions(runId);all.push(...(Array.isArray(ex)?ex:ex?.exceptions||ex?.data||[]));}}}catch{}}setRows(all);}catch(e){setError("Could not load exceptions. Check backend connectivity.");}finally{setLoading(false);}};
  useEffect(()=>{load();},[]);
  const get=(r,...keys)=>keys.map(k=>r[k]).find(v=>v!==undefined&&v!==null)??"—";
  const filtered=rows.filter(r=>JSON.stringify(r).toLowerCase().includes(query.toLowerCase()));
  return <div className="space-y-5"><div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end"><div><h1 className="page-title">Exceptions</h1><p className="page-subtitle">Review rule failures raised by data quality runs.</p></div><Button variant="secondary" onClick={load} disabled={loading}><RefreshCw size={15}/> Refresh</Button></div>
    {error&&<p className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">{error}</p>}
    <Card><div className="flex flex-col gap-3 border-b border-slate-100 p-4 sm:flex-row sm:items-center sm:justify-between"><div className="relative w-full sm:max-w-sm"><Search size={16} className="absolute left-3 top-3 text-slate-400"/><Input className="pl-9" placeholder="Search exceptions..." value={query} onChange={e=>setQuery(e.target.value)}/></div><span className="text-xs text-slate-400">{filtered.length} exceptions</span></div>
    {loading?<p className="p-8 text-center text-sm text-slate-500">Loading exceptions…</p>:filtered.length===0?<div className="p-12 text-center"><AlertCircle className="mx-auto text-slate-300" size={28}/><p className="mt-3 text-sm font-medium text-slate-700">No exceptions to display</p><p className="mt-1 text-xs text-slate-400">Exceptions from processed runs will appear here.</p></div>:
    <div className="overflow-x-auto"><table className="w-full min-w-[750px] text-left text-sm"><thead className="bg-slate-50 text-[11px] uppercase tracking-wide text-slate-500"><tr>{["Exception","Rule","Severity","Owner","Status"].map(x=><th key={x} className="px-5 py-3 font-medium">{x}</th>)}</tr></thead><tbody className="divide-y divide-slate-100">{filtered.map((r,i)=><tr key={get(r,"exceptionId","EXCEPTION_ID")+i}><td className="max-w-xs px-5 py-4"><p className="font-medium text-slate-800">{get(r,"exceptionId","EXCEPTION_ID")}</p><p className="mt-1 truncate text-xs text-slate-400">{get(r,"description","DESCRIPTION")}</p></td><td className="px-5 py-4 text-slate-600">{get(r,"ruleId","RULE_ID")}</td><td className="px-5 py-4"><Badge status={get(r,"severity","SEVERITY")}/></td><td className="px-5 py-4 text-slate-600">{get(r,"assignedTo","ASSIGNED_TO")}</td><td className="px-5 py-4"><Badge status={get(r,"status","STATUS")}/></td></tr>)}</tbody></table></div>}</Card>
  </div>;
}
