import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, RefreshCw, ShieldCheck, ShieldAlert, FileSearch, ChevronDown } from "lucide-react";
import { getBatch, replayBatch } from "../api/batchApi";
import { getScorecard, getRuleResults, getRunExceptions } from "../api/runApi";
import { Badge, Button, Card, CardContent, CardHeader } from "../components/ui/primitives";

const v = (o, ...keys) => keys.map(k => o?.[k]).find(x => x !== undefined && x !== null && x !== "") ?? "—";
const arr = x => Array.isArray(x) ? x : Array.isArray(x?.value) ? x.value : Array.isArray(x?.data) ? x.data : [];
const fmt = x => x && x !== "—" ? new Date(x).toLocaleString() : "—";
const dimensions = [["COMPLETENESS", "Completeness"], ["VALIDITY", "Validity"], ["UNIQUENESS", "Uniqueness"], ["CONSISTENCY", "Consistency"], ["TIMELINESS", "Timeliness"]];
function Metric({ label, value }) { return <div className="rounded-xl border border-slate-100 bg-slate-50 p-4"><p className="text-xs text-slate-500">{label}</p><p className="mt-1 text-xl font-semibold text-slate-900">{value ?? "—"}</p></div> }
function ScoreBar({ label, value }) { const n = Number(value); return <div><div className="mb-1.5 flex justify-between text-xs"><span className="font-medium text-slate-600">{label}</span><span className="font-semibold text-slate-800">{Number.isFinite(n) ? n.toFixed(2) + "%" : "—"}</span></div><div className="h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-electric" style={{ width: `${Math.max(0, Math.min(100, n || 0))}%` }} /></div></div> }
export default function BatchDetails() {

    const [replayFile, setReplayFile] = useState(null);
    const [replayBusy, setReplayBusy] = useState(false);
    const [replayError, setReplayError] = useState("");
    const [replaySuccess, setReplaySuccess] = useState("");
    const { batchId } = useParams();
    const [detail, setDetail] = useState(null), [runId, setRunId] = useState(""), [score, setScore] = useState(null), [rules, setRules] = useState([]), [exceptions, setExceptions] = useState([]), [busy, setBusy] = useState(true), [error, setError] = useState("");
    const runs = arr(detail?.runs);
    const batch = detail?.batch || {};

    const latestRun = runs
        .slice()
        .sort(
            (a, b) =>
                Number(v(b, "RUN_NUMBER", "runNumber", 0)) -
                Number(v(a, "RUN_NUMBER", "runNumber", 0))
        )[0];

    const latestStatus = String(
        v(latestRun, "FINAL_STATUS", "finalStatus")
    ).toUpperCase();

    const canReplay = ["BLOCK", "FAILED"].includes(latestStatus);

    const load = async (preferLatest = false) => {
        setBusy(true); setError("");
        try {
            const d = await getBatch(batchId); setDetail(d);
            const rs = arr(d?.runs); const latest = rs.slice().sort((a, b) => Number(v(b, "RUN_NUMBER", "runNumber", 0)) - Number(v(a, "RUN_NUMBER", "runNumber", 0)))[0];
            // const chosen = rs.find(r => v(r, "RUN_ID", "runId") === runId) || latest;
            const chosen = preferLatest ? latest : rs.find(r => v(r, "RUN_ID", "runId") === runId) || latest;
            const id = v(chosen, "RUN_ID", "runId");
            setRunId(id === "—" ? "" : id);
            if (id === "—") { setScore(null); setRules([]); setExceptions([]); }
        } catch (e) { setError(e?.response?.data?.message || "Could not load batch details. Check the backend and your session."); }
        finally { setBusy(false); }
    };
    useEffect(() => { load(); }, [batchId]);
    useEffect(() => { if (!runId) return; let active = true; (async () => { try { const [s, r, e] = await Promise.all([getScorecard(runId), getRuleResults(runId), getRunExceptions(runId)]); if (active) { setScore(s); setRules(arr(r)); setExceptions(arr(e)); } } catch (err) { if (active) setError(err?.response?.data?.message || "Could not load run scorecard and rule results."); } })(); return () => { active = false; }; }, [runId]);
    const selected = useMemo(() => runs.find(r => v(r, "RUN_ID", "runId") === runId) || runs[0] || {}, [runs, runId]);
    const scoreVal = (key) => v(score, key, key.toLowerCase());
    const failed = rules.filter(r => String(v(r, "RULE_STATUS", "ruleStatus")).toUpperCase() === "FAIL");
    const pub = String(v(score, "PUBLICATION_ALLOWED", "publicationAllowed", selected?.PUBLICATION_ALLOWED)).toLowerCase() === "true";

    const handleReplay = async () => {
        if (!replayFile) {
            setReplayError("Please select a corrected CSV file.");
            return;
        }

        if (!replayFile.name.toLowerCase().endsWith(".csv")) {
            setReplayError("Only CSV files are supported.");
            return;
        }

        if (!canReplay) {
            setReplayError("Only the latest BLOCK or FAILED run can be replayed.");
            return;
        }

        try {
            setReplayBusy(true);
            setReplayError("");
            setReplaySuccess("");

            const result = await replayBatch(batchId, replayFile);

            setReplayFile(null);
            setReplaySuccess(
                result?.message || "Corrected batch replay submitted successfully."
            );

            // Reload batch and automatically select the newly created run.
            await load(true);
        } catch (error) {
            setReplayError(
                error?.response?.data?.error ||
                error?.response?.data?.message ||
                "Replay failed. Please check the backend logs."
            );
        } finally {
            setReplayBusy(false);
        }
    };

    return <div className="space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
            <div><Link to="/batches" className="mb-2 inline-flex items-center gap-2 text-xs font-medium text-slate-500 hover:text-navy"><ArrowLeft size={14} /> Back to batches</Link><h1 className="page-title">Batch details</h1><p className="page-subtitle">{v(batch, "DISPLAY_BATCH_ID", "BATCH_ID")} · {v(batch, "FILE_NAME")}</p></div>
            {/* <Button variant="secondary" onClick={load} disabled={busy}><RefreshCw size={15} /> Refresh</Button> */}
            <div className="flex flex-wrap items-center gap-2">
                {canReplay && (
                    <Button
                    onClick={() => document.getElementById("corrected-replay-file")?.click()}
                    disabled={replayBusy || busy}
                    >
                    <FileSearch size={15} />
                    Correct & Replay
                    </Button>
                )}

                <Button
                    variant="secondary"
                    onClick={() => load()}
                    disabled={busy || replayBusy}
                >
                    <RefreshCw size={15} />
                    Refresh
                </Button>
                </div>
        </div>
        {canReplay && (
  <Card>
    <CardContent>
      <div className="space-y-3">
        <div>
          <h2 className="text-sm font-semibold text-slate-900">
            Correct and replay batch
          </h2>

          <p className="mt-1 text-xs text-slate-500">
            The latest run is {latestStatus}. Upload a corrected CSV
            to create a new processing run. Previous run history
            and exceptions will be preserved.
          </p>
        </div>

        <input
          id="corrected-replay-file"
          type="file"
          accept=".csv,text/csv"
          className="block w-full text-sm text-slate-600 file:mr-3
            file:rounded-lg file:border-0 file:bg-slate-100
            file:px-4 file:py-2 file:text-sm file:font-medium
            file:text-slate-700 hover:file:bg-slate-200"
          onChange={(event) => {
            setReplayFile(event.target.files?.[0] || null);
            setReplayError("");
            setReplaySuccess("");
          }}
        />

        {replayFile && (
          <p className="text-xs text-slate-600">
            Selected file: {replayFile.name}
          </p>
        )}

        {replayError && (
          <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">
            {replayError}
          </p>
        )}

        {replaySuccess && (
          <p className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">
            {replaySuccess}
          </p>
        )}

        <Button
          onClick={handleReplay}
          disabled={!replayFile || replayBusy}
        >
          {replayBusy ? "Processing corrected batch..." : "Submit Corrected Replay"}
        </Button>
      </div>
    </CardContent>
  </Card>
)}
        {error && <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        {busy ? <Card><CardContent><p className="py-10 text-center text-sm text-slate-500">Loading batch details…</p></CardContent></Card> : <>
            <Card><CardHeader><div><h2 className="text-sm font-semibold text-slate-900">Batch information</h2><p className="mt-1 text-xs text-slate-400">Processing lifecycle and source metadata</p></div><Badge status={v(batch, "BATCH_STATUS")} /></CardHeader><CardContent><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <Metric label="Batch reference" value={v(batch, "DISPLAY_BATCH_ID", "BATCH_ID")} /><Metric label="Records" value={v(batch, "RECORD_COUNT")} /><Metric label="Source system" value={v(batch, "SOURCE_SYSTEM")} /><Metric label="Received" value={fmt(v(batch, "RECEIVED_AT"))} />
            </div><div className="mt-4 grid gap-3 text-xs text-slate-500 sm:grid-cols-2"><p><span className="font-semibold text-slate-700">File:</span> {v(batch, "FILE_NAME")}</p><p className="break-all"><span className="font-semibold text-slate-700">Raw S3 key:</span> {v(batch, "RAW_S3_KEY")}</p><p className="break-all sm:col-span-2"><span className="font-semibold text-slate-700">Checksum:</span> {v(batch, "SOURCE_CHECKSUM")}</p></div></CardContent></Card>
            <Card><CardHeader><div><h2 className="text-sm font-semibold text-slate-900">Processing runs</h2><p className="mt-1 text-xs text-slate-400">Select a run to inspect its quality decision</p></div><span className="text-xs text-slate-400">{runs.length} runs</span></CardHeader><CardContent><div className="space-y-2">{runs.map(r => { const id = v(r, "RUN_ID", "runId"); const active = id === runId; return <button key={id} onClick={() => setRunId(id)} className={`flex w-full flex-wrap items-center justify-between gap-3 rounded-lg border p-3 text-left ${active ? "border-blue-300 bg-blue-50/60" : "border-slate-100 hover:bg-slate-50"}`}><div><p className="text-sm font-semibold text-slate-800">Run {v(r, "RUN_NUMBER")} · {v(r, "RUN_TYPE")}</p><p className="mt-1 text-xs text-slate-400">{id} · {fmt(v(r, "EXECUTED_AT"))}</p></div><div className="flex items-center gap-3"><span className="text-sm font-semibold">{v(r, "OVERALL_SCORE")}%</span><Badge status={v(r, "FINAL_STATUS")} /></div></button> })}</div></CardContent></Card>
            {score && <><div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4"><Metric label="Overall DQ score" value={`${v(score, "OVERALL_SCORE")}%`} /><Metric label="Critical failures" value={v(score, "CRITICAL_FAILURES")} /><Metric label="High failures" value={v(score, "HIGH_FAILURES")} /><Metric label="Exceptions" value={exceptions.length} /></div>
                <Card><CardHeader><div><h2 className="text-sm font-semibold text-slate-900">Quality scorecard</h2><p className="mt-1 text-xs text-slate-400">Weighted scores across the five required dimensions</p></div><Badge status={v(score, "FINAL_STATUS")} /></CardHeader><CardContent><div className="grid gap-6 md:grid-cols-2"><div className="space-y-4">{dimensions.map(([k, label]) => <ScoreBar key={k} label={label} value={v(score, `${k}_SCORE`, `${k.toLowerCase()}_score`)} />)}</div><div className={`flex flex-col justify-center rounded-xl p-5 ${pub ? "bg-emerald-50" : "bg-red-50"}`}><div className="flex items-center gap-2">{pub ? <ShieldCheck className="text-emerald-700" /> : <ShieldAlert className="text-red-700" />}<p className={`text-sm font-semibold ${pub ? "text-emerald-800" : "text-red-800"}`}>{pub ? "Publication permitted" : "Publication blocked"}</p></div><p className={`mt-2 text-xs leading-5 ${pub ? "text-emerald-700" : "text-red-700"}`}>{pub ? "This run passed the publication gate and may be published." : "This run is not eligible for publication. Resolve blocking failures and submit a corrected replay."}</p><p className="mt-4 text-xs text-slate-500">Run ID: {runId}</p><p className="mt-1 text-xs text-slate-500">Executed: {fmt(v(score, "EXECUTED_AT"))}</p></div></div></CardContent></Card>
                <Card><CardHeader><div><h2 className="text-sm font-semibold text-slate-900">Rule results</h2><p className="mt-1 text-xs text-slate-400">Individual validation outcomes for this run</p></div><span className="text-xs text-slate-400">{rules.length} rules · {failed.length} failed</span></CardHeader><div className="overflow-x-auto"><table className="w-full min-w-[900px] text-left text-sm"><thead className="bg-slate-50 text-[11px] uppercase tracking-wide text-slate-500"><tr>{["Rule", "Dimension", "Severity", "Blocking", "Checked", "Passed", "Failed", "Failure rate", "Status"].map(x => <th key={x} className="px-4 py-3 font-medium">{x}</th>)}</tr></thead><tbody className="divide-y divide-slate-100">{rules.map(r => <tr key={v(r, "RULE_ID")} className="hover:bg-slate-50/70"><td className="px-4 py-3"><p className="font-semibold text-slate-800">{v(r, "RULE_ID")}</p><p className="mt-1 text-xs text-slate-500">{v(r, "RULE_NAME")}</p></td><td className="px-4 py-3 text-xs text-slate-600">{v(r, "DIMENSION")}</td><td className="px-4 py-3"><Badge status={v(r, "SEVERITY")} /></td><td className="px-4 py-3 text-xs">{String(v(r, "IS_BLOCKING")).toLowerCase() === "true" ? "Yes" : "No"}</td><td className="px-4 py-3 tabular-nums">{v(r, "CHECKED_COUNT")}</td><td className="px-4 py-3 tabular-nums">{v(r, "PASSED_COUNT")}</td><td className="px-4 py-3 tabular-nums">{v(r, "FAILED_COUNT")}</td><td className="px-4 py-3 tabular-nums">{v(r, "FAILURE_RATE")}%</td><td className="px-4 py-3"><Badge status={v(r, "RULE_STATUS")} /></td></tr>)}</tbody></table></div></Card>
                <Card><CardHeader><div><h2 className="text-sm font-semibold text-slate-900">Exceptions from this run</h2><p className="mt-1 text-xs text-slate-400">Failures requiring investigation or remediation</p></div><span className="text-xs text-slate-400">{exceptions.length} exceptions</span></CardHeader>{exceptions.length ? <div className="divide-y divide-slate-100">{exceptions.slice(0, 8).map(e => <div key={v(e, "EXCEPTION_ID")} className="flex flex-wrap items-start justify-between gap-2 px-5 py-3"><div className="min-w-0"><p className="text-xs font-semibold text-navy">{v(e, "DISPLAY_EXCEPTION_ID", "EXCEPTION_ID")} · {v(e, "RULE_ID")}</p><p className="mt-1 text-xs leading-5 text-slate-600">{v(e, "DESCRIPTION")}</p></div><Badge status={v(e, "SEVERITY")} /></div>)}</div> : <CardContent><p className="text-sm text-slate-500">No exceptions for this run.</p></CardContent>}</Card>
            </>}
        </>}
    </div>;
}
