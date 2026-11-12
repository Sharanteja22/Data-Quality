import { useEffect, useMemo, useState } from "react"; import { AlertCircle, RefreshCw, Search, Save, X } from "lucide-react";
import { getBatches, getBatch } from "../api/batchApi"; import { getRunExceptions } from "../api/runApi"; import { updateException } from "../api/exceptionApi";
import { Badge, Button, Card, Input } from "../components/ui/primitives";
const v = (o, ...k) => k.map(x => o?.[x]).find(x => x !== undefined && x !== null && x !== "") ?? "—";
const arr = x => Array.isArray(x) ? x : Array.isArray(x?.value) ? x.value : Array.isArray(x?.data) ? x.data : [];
export default function Exceptions() {
    const [rows, setRows] = useState([]), [q, setQ] = useState(""), [severity, setSeverity] = useState("ALL"), [status, setStatus] = useState("ALL"), [busy, setBusy] = useState(true), [error, setError] = useState(""), [selected, setSelected] = useState(null), [nextStatus, setNextStatus] = useState("OPEN"), [notes, setNotes] = useState(""), [assigned, setAssigned] = useState(""), [saving, setSaving] = useState(false), [saveError, setSaveError] = useState("");
    const load = async () => { setBusy(true); setError(""); try { const batches = arr(await getBatches()); const all = []; for (const b of batches) { const id = v(b, "BATCH_ID", "batchId"); if (id === "—") continue; try { const d = await getBatch(id); for (const r of arr(d?.runs)) { const rid = v(r, "RUN_ID", "runId"); if (rid !== "—") { const es = arr(await getRunExceptions(rid)); all.push(...es.map(e => ({ ...e, _batchRef: v(d?.batch, "DISPLAY_BATCH_ID", "BATCH_ID"), _fileName: v(d?.batch, "FILE_NAME") }))); } } } catch { } } const unique = [...new Map(all.map(e => [v(e, "EXCEPTION_ID", "exceptionId"), e])).values()]; setRows(unique); } catch (e) { setError("Could not load exception data. Check backend connectivity."); } finally { setBusy(false); } };
    useEffect(() => { load(); }, []);
    const filtered = useMemo(() => rows.filter(x => { const match = JSON.stringify(x).toLowerCase().includes(q.toLowerCase()); const sev = severity === "ALL" || String(v(x, "SEVERITY")).toUpperCase() === severity; const st = status === "ALL" || String(v(x, "STATUS")).toUpperCase() === status; return match && sev && st; }), [rows, q, severity, status]);
    const openEdit = x => { setSelected(x); setNextStatus(v(x, "STATUS") === "—" ? "OPEN" : v(x, "STATUS")); setNotes(v(x, "RESOLUTION_NOTES") === "—" ? "" : v(x, "RESOLUTION_NOTES")); setAssigned(v(x, "ASSIGNED_TO") === "—" ? "" : v(x, "ASSIGNED_TO")); setSaveError(""); };
    const save = async () => { setSaving(true); setSaveError(""); try { const id = v(selected, "EXCEPTION_ID", "exceptionId"); await updateException(id, { status: nextStatus, resolutionNotes: notes, assignedTo: assigned }); setSelected(null); await load(); } catch (e) { setSaveError(e?.response?.data?.message || "Could not update exception. Verify the API payload/permissions."); } finally { setSaving(false); } };
    return <div className="space-y-5">
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end"><div><h1 className="page-title">Exceptions</h1><p className="page-subtitle">Investigate rule failures, manage ownership and record resolution notes.</p></div><Button variant="secondary" onClick={load} disabled={busy}><RefreshCw size={15} /> Refresh</Button></div>
        {error && <p className="rounded-lg bg-amber-50 p-3 text-sm text-amber-800">{error}</p>}
        <Card><div className="flex flex-col gap-3 border-b border-slate-100 p-4 lg:flex-row lg:items-center"><div className="relative w-full lg:max-w-sm"><Search size={16} className="absolute left-3 top-3 text-slate-400" /><Input className="pl-9" placeholder="Search exception, rule, batch or owner…" value={q} onChange={e => setQ(e.target.value)} /></div><div className="flex flex-wrap gap-2"><select className="h-10 rounded-lg border border-slate-200 bg-white px-3 text-sm" value={severity} onChange={e => setSeverity(e.target.value)}><option value="ALL">All severities</option>{["CRITICAL", "HIGH", "MEDIUM", "LOW"].map(x => <option key={x}>{x}</option>)}</select><select className="h-10 rounded-lg border border-slate-200 bg-white px-3 text-sm" value={status} onChange={e => setStatus(e.target.value)}><option value="ALL">All statuses</option>{["OPEN", "IN_PROGRESS", "RESOLVED"].map(x => <option key={x}>{x}</option>)}</select></div><span className="text-xs text-slate-400 lg:ml-auto">{filtered.length} exceptions</span></div>
            {busy ? <p className="p-8 text-center text-sm text-slate-500">Loading exceptions…</p> : !filtered.length ? <div className="p-12 text-center"><AlertCircle className="mx-auto text-slate-300" size={28} /><p className="mt-3 text-sm font-medium text-slate-700">No exceptions found</p><p className="mt-1 text-xs text-slate-400">Try changing your filters or process a batch.</p></div> : <div className="overflow-x-auto"><table className="w-full min-w-[1050px] text-left text-sm"><thead className="bg-slate-50 text-[11px] uppercase tracking-wide text-slate-500"><tr>
                {["Exception reference", "Rule", "Severity", "Batch", "Assigned team", "Status", "Created", "Action"].map(x => (
  <th
    key={x}
    className={`px-4 py-3 font-medium ${
      x === "Action"
        ? "sticky right-0 z-20 bg-slate-50 text-right"
        : ""
    }`}
  >
    {x}
  </th>
))}
</tr></thead><tbody className="divide-y divide-slate-100">{filtered.map((x, i) => <tr key={v(x, "EXCEPTION_ID", "exceptionId") + i} className="hover:bg-slate-50/70"><td className="px-4 py-3 font-semibold text-navy">{v(x, "DISPLAY_EXCEPTION_ID", "EXCEPTION_ID")}</td><td className="px-4 py-3 text-slate-600">{v(x, "RULE_ID")}</td><td className="px-4 py-3"><Badge status={v(x, "SEVERITY")} /></td><td className="px-4 py-3 text-xs text-slate-600">{v(x, "_batchRef")}</td><td className="px-4 py-3 text-xs text-slate-600">{v(x, "ASSIGNED_TO")}</td><td className="px-4 py-3"><Badge status={v(x, "STATUS")} /></td><td className="px-4 py-3 text-xs text-slate-500">{v(x, "CREATED_AT") !== "—" ? new Date(v(x, "CREATED_AT")).toLocaleString() : "—"}</td>
<td className="sticky right-0 z-10 bg-white px-4 py-3 text-right">
  <Button
    size="sm"
    variant="secondary"
    onClick={() => openEdit(x)}
  >
    Manage
  </Button>
</td>
    </tr>)}</tbody></table></div>}
        </Card>
        {selected && <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4"><div className="max-h-[90vh] w-full max-w-xl overflow-y-auto rounded-2xl bg-white shadow-xl"><div className="flex items-center justify-between border-b border-slate-100 p-5"><div><h2 className="text-base font-semibold text-slate-900">Manage exception</h2><p className="mt-1 text-xs text-slate-400">{v(selected, "DISPLAY_EXCEPTION_ID", "EXCEPTION_ID")}</p></div><button onClick={() => setSelected(null)} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"><X size={18} /></button></div><div className="space-y-4 p-5"><div className="rounded-lg bg-slate-50 p-3"><p className="text-xs font-semibold text-slate-700">{v(selected, "RULE_ID")} · {v(selected, "SEVERITY")}</p><p className="mt-2 text-sm leading-6 text-slate-600">{v(selected, "DESCRIPTION")}</p></div><label className="block space-y-1.5"><span className="text-xs font-medium text-slate-600">Status</span><select className="h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm" value={nextStatus} onChange={e => setNextStatus(e.target.value)}>{["OPEN", "IN_PROGRESS", "RESOLVED"].map(x => <option key={x} value={x}>{x.replace("_", " ")}</option>)}</select></label><label className="block space-y-1.5"><span className="text-xs font-medium text-slate-600">Assigned team</span><Input value={assigned} onChange={e => setAssigned(e.target.value)} placeholder="e.g. Transaction Team" /></label><label className="block space-y-1.5"><span className="text-xs font-medium text-slate-600">Resolution notes</span><textarea rows={4} className="w-full rounded-lg border border-slate-200 p-3 text-sm outline-none focus:border-electric" value={notes} onChange={e => setNotes(e.target.value)} placeholder="Document investigation and remediation…" /></label>{saveError && <p className="rounded-lg bg-red-50 p-3 text-xs text-red-700">{saveError}</p>}<div className="flex justify-end gap-2"><Button variant="secondary" onClick={() => setSelected(null)}>Cancel</Button><Button onClick={save} disabled={saving}><Save size={15} />{saving ? "Saving…" : "Save changes"}</Button></div></div></div></div>}
        <p className="text-xs text-slate-400">Human-readable exception references are displayed; internal UUIDs remain the API identifiers.</p>
    </div>;
}
