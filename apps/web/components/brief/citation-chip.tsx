"use client";

import { FileText } from "lucide-react";
import { useState } from "react";

import type { ChunkRef } from "@/lib/api-client";
import { cn } from "@/lib/utils";

type Props = {
  refs: ChunkRef[];
  className?: string;
};

/**
 * Inline cluster of citation chips with hover-to-reveal source snippets.
 *
 * Hover/focus reveals a popover containing the document name and the
 * chunk snippet so users can audit each claim without leaving the brief.
 */
export function CitationChips({ refs, className }: Props) {
  if (refs.length === 0) {
    return (
      <span className={cn("inline-flex items-center text-xs text-muted-foreground", className)}>
        — uncited
      </span>
    );
  }
  return (
    <span className={cn("inline-flex flex-wrap items-center gap-1", className)}>
      {refs.map((r, i) => (
        <CitationChip key={r.chunk_id} ref_={r} index={i + 1} />
      ))}
    </span>
  );
}

function CitationChip({ ref_, index }: { ref_: ChunkRef; index: number }) {
  const [open, setOpen] = useState(false);
  return (
    <span className="relative inline-flex">
      <button
        type="button"
        className={cn(
          "inline-flex items-center gap-0.5 rounded-full border px-1.5 py-0.5 text-[10px] font-medium",
          "border-brand-accent/40 bg-brand-accent/10 text-brand-accent",
          "hover:bg-brand-accent/20 focus:outline-none focus:ring-1 focus:ring-brand-accent",
        )}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        aria-label={`Source ${index}: ${ref_.document_filename ?? "unknown"}`}
      >
        <FileText className="size-2.5" aria-hidden />
        {index}
      </button>
      {open && (
        <span
          role="tooltip"
          className={cn(
            "absolute bottom-full left-1/2 z-20 mb-2 w-72 -translate-x-1/2 rounded-md border",
            "border-brand-hairline bg-white p-3 text-left shadow-lg",
          )}
        >
          <span className="block text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
            {ref_.document_filename ?? "source"}
          </span>
          <span className="mt-1 block text-xs leading-relaxed text-brand-slate">
            {ref_.snippet ?? "(no snippet)"}
          </span>
        </span>
      )}
    </span>
  );
}
