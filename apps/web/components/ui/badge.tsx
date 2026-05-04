import * as React from "react";

import { cn } from "@/lib/utils";

type BadgeVariant = "default" | "muted" | "accent" | "success" | "warning" | "danger";

const variantClasses: Record<BadgeVariant, string> = {
  default: "bg-brand-obsidian text-white",
  muted: "bg-brand-fog text-brand-slate border border-brand-hairline",
  accent: "bg-brand-accent/15 text-brand-accent border border-brand-accent/30",
  success: "bg-emerald-50 text-emerald-700 border border-emerald-200",
  warning: "bg-amber-50 text-amber-700 border border-amber-200",
  danger: "bg-red-50 text-red-700 border border-red-200",
};

export function Badge({
  children,
  variant = "default",
  className,
}: {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium",
        variantClasses[variant],
        className,
      )}
    >
      {children}
    </span>
  );
}
