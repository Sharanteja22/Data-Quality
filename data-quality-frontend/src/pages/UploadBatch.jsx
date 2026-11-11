import { useRef, useState } from "react";
import { FileUp, FileText, CheckCircle2, AlertCircle, X } from "lucide-react";
import { uploadBatch } from "../api/batchApi";
import Button from "../components/ui/Button";
import { Card, CardContent } from "../components/ui/Card";
import Badge from "../components/ui/Badge";

export default function UploadBatch() {
  const inputRef=useRef(null); const [file,setFile]=useState(null); const [drag,setDrag]=useState(false); const [busy,setBusy]=useState(false); const [result,setResult]=useState(null); const [error,setError]=useState("");
  const choose=f=>{if(!f)return;setError("");setResult(null);if(!f.name.toLowerCase().endsWith(".csv")){setFile(null);setError("Please select a .csv file.");return;}if(f.size>10*1024*1024){setFile(null);setError("File size must be 10 MB or less.");return;}setFile(f);};
  const submit=async()=>{if(!file)return;setBusy(true);setError("");setResult(null);try{setResult(await uploadBatch(file));}catch(e){setError(e.response?.data?.message||"Upload failed. Confirm the backend is running and try again.");}finally{setBusy(false);}};
  return <div className="mx-auto max-w-3xl space-y-5">
    <div><h1 className="page-title">Upload batch</h1><p className="page-subtitle">Submit a transaction CSV for data quality validation.</p></div>
    <Card><CardContent className="space-y-5">
      <div><h2 className="section-title">Transaction file</h2><p className="mt-1 text-xs text-slate-400">CSV format · Maximum file size 10 MB</p></div>
      <button type="button" onClick={()=>inputRef.current?.click()} onDragOver={e=>{e.preventDefault();setDrag(true);}} onDragLeave={()=>setDrag(false)} onDrop={e=>{e.preventDefault();setDrag(false);choose(e.dataTransfer.files?.[0]);}} className={`flex min-h-56 w-full flex-col items-center justify-center rounded-xl border-2 border-dashed px-5 text-center transition ${drag?"border-electric bg-blue-50":"border-slate-200 bg-slate-50 hover:border-blue-300 hover:bg-blue-50/50"}`}>
        <div className="grid h-12 w-12 place-items-center rounded-xl bg-blue-100 text-electric"><FileUp size={23}/></div><p className="mt-4 text-sm font-semibold text-slate-800">Drop your CSV file here</p><p className="mt-1 text-xs text-slate-500">or <span className="font-semibold text-electric">browse files</span></p><p className="mt-3 text-[11px] text-slate-400">Only .csv files are accepted</p>
      </button>
      <input ref={inputRef} type="file" accept=".csv,text/csv" className="hidden" onChange={e=>choose(e.target.files?.[0])}/>
      {file&&<div className="flex items-center gap-3 rounded-lg border border-slate-200 p-3"><div className="rounded-lg bg-blue-50 p-2 text-electric"><FileText size={18}/></div><div className="min-w-0 flex-1"><p className="truncate text-sm font-medium text-slate-800">{file.name}</p><p className="text-xs text-slate-400">{(file.size/1024).toFixed(1)} KB</p></div><button onClick={()=>setFile(null)} className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100" aria-label="Remove file"><X size={16}/></button></div>}
      {error&&<div className="flex gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"><AlertCircle size={17} className="mt-0.5 shrink-0"/>{error}</div>}
      {result&&<div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4"><div className="flex items-center gap-2 text-sm font-semibold text-emerald-800"><CheckCircle2 size={17}/>Upload processed</div><pre className="mt-3 overflow-auto text-xs text-emerald-900">{JSON.stringify(result,null,2)}</pre></div>}
      <div className="flex flex-col-reverse justify-end gap-2 border-t border-slate-100 pt-4 sm:flex-row"><Button variant="secondary" onClick={()=>{setFile(null);setResult(null);setError("");}}>Clear</Button><Button onClick={submit} disabled={!file||busy}>{busy?"Processing…": "Upload and validate"} <FileUp size={15}/></Button></div>
    </CardContent></Card>
    <p className="text-xs leading-5 text-slate-400">The backend performs schema validation, rule execution, scoring and publication decisions. The frontend does not make data quality decisions.</p>
  </div>;
}
