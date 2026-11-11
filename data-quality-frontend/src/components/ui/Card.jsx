import { cn } from "./utils";

export function Card({ className, children }) {
  return <section className={cn("rounded-xl border border-slate-200 bg-white shadow-soft", className)}>{children}</section>;
}
export function CardHeader({ className, children }) {
  return <div className={cn("flex items-center justify-between gap-3 border-b border-slate-100 px-5 py-4", className)}>{children}</div>;
}
export function CardContent({ className, children }) {
  return <div className={cn("p-5", className)}>{children}</div>;
}
