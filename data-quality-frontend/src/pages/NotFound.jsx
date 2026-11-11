import { Link } from "react-router-dom";
export default function NotFound(){return <div className="py-20 text-center"><p className="text-5xl font-bold text-navy">404</p><p className="mt-3 text-slate-600">Page not found</p><Link to="/" className="mt-5 inline-block text-sm font-semibold text-electric">Back to overview</Link></div>;}
