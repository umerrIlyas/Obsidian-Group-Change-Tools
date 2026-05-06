"use client";

import { ChevronDown } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { BriefSummary } from "@/lib/api-client";
import { cn } from "@/lib/utils";

type Props = {
  versions: BriefSummary[];
  selectedId: string | null;
  onSelect: (briefId: string) => void;
};

export function BriefVersionSelector({ versions, selectedId, onSelect }: Props) {
  const [open, setOpen] = useState(false);
  if (versions.length === 0) return null;
  const current = versions.find((v) => v.id === selectedId) ?? versions[0];

  return (
    <div className="relative">
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        v{current.version}
        {versions.length > 1 && (
          <Badge variant="muted" className="ml-1">
            {versions.length} versions
          </Badge>
        )}
        <ChevronDown className="size-3" aria-hidden />
      </Button>
      {open && (
        <div
          className={cn(
            "absolute right-0 top-full z-30 mt-1 w-72 overflow-hidden rounded-md border border-brand-hairline bg-white shadow-lg",
          )}
        >
          <ul className="max-h-72 overflow-y-auto py-1 text-sm">
            {versions.map((v) => (
              <li key={v.id}>
                <button
                  type="button"
                  onClick={() => {
                    onSelect(v.id);
                    setOpen(false);
                  }}
                  className={cn(
                    "flex w-full items-center justify-between gap-2 px-3 py-2 text-left",
                    "hover:bg-brand-fog/60",
                    v.id === current.id && "bg-brand-fog/40",
                  )}
                >
                  <div className="flex flex-col">
                    <span className="font-medium text-brand-obsidian">
                      v{v.version}
                    </span>
                    <span className="text-[11px] text-muted-foreground">
                      {new Date(v.created_at).toLocaleString()}
                    </span>
                  </div>
                  {v.id === current.id && (
                    <Badge variant="accent">selected</Badge>
                  )}
                  {v.status === "failed" && (
                    <Badge variant="danger">failed</Badge>
                  )}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
