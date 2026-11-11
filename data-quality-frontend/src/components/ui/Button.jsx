import { forwardRef } from "react";
import { cn } from "./utils";

const Button = forwardRef(function Button({ className, variant = "primary", size = "md", ...props }, ref) {
  const variants = {
    primary: "bg-electric text-white hover:bg-blue-600 shadow-sm",
    secondary: "bg-white text-slate-700 border border-slate-200 hover:bg-slate-50",
    ghost: "text-slate-600 hover:bg-slate-100",
    outline: "border border-blue-200 text-navy bg-white hover:bg-blue-50"
  };
  const sizes = { sm: "h-8 px-3 text-xs", md: "h-10 px-4 text-sm", lg: "h-11 px-5 text-sm" };
  return <button ref={ref} className={cn("inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed", variants[variant], sizes[size], className)} {...props} />;
});
export default Button;
