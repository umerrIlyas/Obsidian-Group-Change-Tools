import type { CSSProperties, ReactNode } from "react";

import type { BrandProfile } from "@/lib/api-client";

/**
 * Wraps children in a div whose inline style overrides the brand CSS variables.
 *
 * Re-themes the entire UI tree underneath because every brand colour in
 * Tailwind is read through ``var(--brand-*)``.
 */
export function BrandVars({
  profile,
  children,
}: {
  profile: BrandProfile | null;
  children: ReactNode;
}) {
  if (!profile) return <>{children}</>;
  const style: CSSProperties = {
    ["--brand-obsidian" as keyof CSSProperties]: profile.primary_color,
    ["--brand-slate" as keyof CSSProperties]: profile.secondary_color,
    ["--brand-accent" as keyof CSSProperties]: profile.accent_color,
    ["--brand-stone" as keyof CSSProperties]: profile.neutrals.stone,
    ["--brand-hairline" as keyof CSSProperties]: profile.neutrals.hairline,
    ["--brand-fog" as keyof CSSProperties]: profile.neutrals.fog,
    ["--font-display" as keyof CSSProperties]: `"${profile.font_heading}", "Aptos Display", system-ui, sans-serif`,
    ["--font-sans" as keyof CSSProperties]: `"${profile.font_body}", "Aptos", system-ui, sans-serif`,
  } as CSSProperties;
  return <div style={style}>{children}</div>;
}
