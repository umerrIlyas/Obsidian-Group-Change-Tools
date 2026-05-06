import { ChevronDown, ChevronRight, Loader2, Wrench } from "lucide-react";
import { useState } from "react";

import { cn } from "@/lib/utils";

type Status = "running" | "done";

type Props = {
  name: string;
  args: Record<string, unknown>;
  output?: string | null;
  status: Status;
};

const PRETTY: Record<string, string> = {
  retrieve_evidence: "Searching evidence",
  read_brief_section: "Reading brief section",
  update_brief_section: "Updating brief section",
  regenerate_deck: "Regenerating deck",
  list_risks: "Listing risks",
  list_kpis: "Listing KPIs",
  list_stakeholders: "Listing stakeholders",
};

export function ToolCallCard({ name, args, output, status }: Props) {
  const [open, setOpen] = useState(false);
  const label = PRETTY[name] ?? name;

  return (
    <div className="rounded-md border border-brand-hairline bg-brand-fog/40 text-xs">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={cn(
          "flex w-full items-center gap-2 px-3 py-2 text-left",
          "hover:bg-brand-fog/70",
        )}
      >
        {open ? (
          <ChevronDown className="size-3 text-muted-foreground" aria-hidden />
        ) : (
          <ChevronRight className="size-3 text-muted-foreground" aria-hidden />
        )}
        {status === "running" ? (
          <Loader2 className="size-3 animate-spin text-brand-accent" aria-hidden />
        ) : (
          <Wrench className="size-3 text-brand-accent" aria-hidden />
        )}
        <span className="font-medium text-brand-obsidian">{label}</span>
        <span className="ml-auto font-mono text-[10px] text-muted-foreground">
          {name}
        </span>
      </button>
      {open && (
        <div className="border-t border-brand-hairline bg-white px-3 py-2 font-mono text-[11px]">
          {Object.keys(args).length > 0 && (
            <div className="mb-2">
              <div className="mb-1 text-[10px] uppercase tracking-wide text-muted-foreground">
                Arguments
              </div>
              <pre className="max-h-40 overflow-auto whitespace-pre-wrap text-brand-slate">
                {JSON.stringify(args, null, 2)}
              </pre>
            </div>
          )}
          <div>
            <div className="mb-1 text-[10px] uppercase tracking-wide text-muted-foreground">
              Result
            </div>
            <pre className="max-h-60 overflow-auto whitespace-pre-wrap text-brand-slate">
              {status === "running" ? "(running…)" : output || "(empty)"}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
