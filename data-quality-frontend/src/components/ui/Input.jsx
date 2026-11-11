export default function Input({ className = "", ...props }) {
  return <input className={`h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-800 outline-none placeholder:text-slate-400 focus:border-electric focus:ring-2 focus:ring-blue-100 ${className}`} {...props} />;
}
