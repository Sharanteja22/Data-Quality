import { useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { Activity, AlertCircle, BarChart3, ChevronLeft, ChevronRight, Database, FileUp, LayoutDashboard, Menu, X } from "lucide-react";

const links = [
  { to: "/", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/batches", label: "Batches", icon: Database },
  { to: "/upload", label: "Upload batch", icon: FileUp },
  { to: "/exceptions", label: "Exceptions", icon: AlertCircle }
];

function SidebarContent({ onNavigate }) {
  return <>
    <div className="flex h-16 items-center gap-3 border-b border-white/10 px-5">
      <div className="grid h-9 w-9 place-items-center rounded-xl bg-blue-500"><Activity size={19} /></div>
      <div><p className="text-sm font-semibold tracking-wide text-white">Data Quality</p><p className="text-[11px] text-blue-200">Operations console</p></div>
    </div>
    <div className="px-3 pt-7">
      <p className="px-3 pb-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-blue-300">Workspace</p>
      <nav className="space-y-1">
        {links.map(({ to, label, icon: Icon, end }) => <NavLink key={to} to={to} end={end} onClick={onNavigate}
          className={({ isActive }) => `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition ${isActive ? "bg-blue-600 text-white shadow-sm" : "text-blue-100 hover:bg-white/10 hover:text-white"}`}>
          <Icon size={17} strokeWidth={1.9} />{label}
        </NavLink>)}
      </nav>
    </div>
    <div className="mt-auto p-4">
      <div className="rounded-xl border border-white/10 bg-white/5 p-3">
        <div className="flex items-center gap-2 text-xs font-medium text-blue-100"><span className="h-2 w-2 rounded-full bg-emerald-400" />System workspace</div>
        <p className="mt-1.5 text-[11px] leading-5 text-blue-200/70">Operational Data Quality Scorecard</p>
      </div>
    </div>
  </>;
}

export default function AppShell({ children }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const current = links.find(l => l.to === location.pathname);
  const title = current?.label || "Workspace";
  return <div className="min-h-screen bg-ice">
    <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col bg-navy text-white lg:flex"><SidebarContent /></aside>
    {mobileOpen && <div className="fixed inset-0 z-40 lg:hidden">
      <button aria-label="Close menu" className="absolute inset-0 bg-slate-950/40" onClick={() => setMobileOpen(false)} />
      <aside className="relative flex h-full w-72 flex-col bg-navy text-white"><div className="flex justify-end p-3"><button onClick={() => setMobileOpen(false)} aria-label="Close menu"><X /></button></div><SidebarContent onNavigate={() => setMobileOpen(false)} /></aside>
    </div>}
    <div className="lg:pl-64">
      <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-200 bg-white/90 px-4 backdrop-blur sm:px-7">
        <div className="flex items-center gap-3">
          <button className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 lg:hidden" onClick={() => setMobileOpen(true)} aria-label="Open menu"><Menu size={20} /></button>
          <div><p className="text-sm font-semibold text-slate-800">{title}</p><p className="hidden text-[11px] text-slate-400 sm:block">Data quality monitoring</p></div>
        </div>
        <div className="flex items-center gap-3">
          <span className="hidden text-xs text-slate-500 sm:inline">Environment</span>
          <span className="rounded-full border border-blue-100 bg-blue-50 px-2.5 py-1 text-[11px] font-semibold text-navy">LOCAL</span>
          <div className="grid h-8 w-8 place-items-center rounded-full bg-blue-100 text-xs font-semibold text-navy">ST</div>
        </div>
      </header>
      <main className="mx-auto max-w-[1500px] p-4 sm:p-6 lg:p-8">{children}</main>
    </div>
  </div>;
}
