const styles = {
  PASS: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  WARN: "bg-amber-50 text-amber-700 ring-amber-600/20",
  BLOCK: "bg-red-50 text-red-700 ring-red-600/20",
  FAILED: "bg-slate-100 text-slate-700 ring-slate-500/20",
  RECEIVED: "bg-blue-50 text-blue-700 ring-blue-600/20",
  PROCESSED: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  OPEN: "bg-amber-50 text-amber-700 ring-amber-600/20",
  RESOLVED: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  IN_PROGRESS: "bg-blue-50 text-blue-700 ring-blue-600/20"
};
export default function Badge({ status = "UNKNOWN" }) {
  return <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-semibold ring-1 ring-inset ${styles[status] || "bg-slate-100 text-slate-600 ring-slate-500/20"}`}>{status.replaceAll("_", " ")}</span>;
}
