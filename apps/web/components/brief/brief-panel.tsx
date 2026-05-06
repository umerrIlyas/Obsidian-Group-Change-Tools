"use client";

import { CheckCircle2, FileText, Loader2, Sparkles, XCircle } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { BriefViewer } from "@/components/brief/brief-viewer";
import { DeckPanel } from "@/components/brief/deck-panel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ApiError,
  type Brief,
  type BriefProgressEvent,
  api,
  streamBriefGeneration,
} from "@/lib/api-client";
import { cn } from "@/lib/utils";

type ProgressItem = {
  kind: BriefProgressEvent["kind"];
  message: string;
  ts: number;
};

const KIND_LABEL: Record<BriefProgressEvent["kind"], string> = {
  started: "Started",
  start: "Loading context",
  context_loaded: "Loaded project + brand",
  evidence_retrieved: "Retrieved evidence",
  section_drafted: "Drafted sections",
  validation_failed: "Validation failed — retrying",
  validated: "Validated",
  citations_scored: "Scored citations",
  conflicts_detected: "Detected conflicts",
  persisted: "Saved",
  error: "Error",
  done: "Done",
};

export function BriefPanel({ projectId }: { projectId: string }) {
  const [latest, setLatest] = useState<Brief | null>(null);
  const [progress, setProgress] = useState<ProgressItem[]>([]);
  const [running, setRunning] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Load latest brief if there is one already.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const list = await api.briefs.list(projectId);
        if (cancelled || list.length === 0) return;
        const latest = await api.briefs.get(list[0].id);
        if (!cancelled) setLatest(latest);
      } catch (e) {
        if (e instanceof ApiError && e.status !== 404) {
          setErrorMsg(e.message);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  async function onGenerate() {
    setRunning(true);
    setProgress([]);
    setErrorMsg(null);
    const abort = new AbortController();
    abortRef.current = abort;
    let briefId: string | null = null;
    try {
      for await (const ev of streamBriefGeneration(projectId, abort.signal)) {
        const message = ev.message ?? KIND_LABEL[ev.kind] ?? ev.kind;
        setProgress((prev) => [...prev, { kind: ev.kind, message, ts: Date.now() }]);
        if (ev.brief_id) briefId = ev.brief_id;
        if (ev.kind === "error") {
          setErrorMsg(message);
        }
      }
      if (briefId) {
        const fresh = await api.briefs.get(briefId);
        setLatest(fresh);
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Stream failed";
      setErrorMsg(msg);
      setProgress((prev) => [
        ...prev,
        { kind: "error", message: msg, ts: Date.now() },
      ]);
    } finally {
      setRunning(false);
      abortRef.current = null;
    }
  }

  function onCancel() {
    abortRef.current?.abort();
  }

  return (
    <section className="flex flex-col gap-4">
      <header className="flex items-end justify-between gap-3">
        <div>
          <h2 className="font-display text-xl font-semibold tracking-tight">
            Change strategy brief
          </h2>
          <p className="text-sm text-muted-foreground">
            One agent run produces a structured brief grounded in your uploaded
            documents. Each section cites the chunks it draws on.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {running ? (
            <Button variant="outline" size="sm" onClick={onCancel}>
              Cancel
            </Button>
          ) : null}
          <Button onClick={onGenerate} disabled={running}>
            {running ? (
              <>
                <Loader2 className="size-4 animate-spin" aria-hidden /> Generating…
              </>
            ) : (
              <>
                <Sparkles className="size-4" aria-hidden />
                {latest ? "Regenerate brief" : "Generate brief"}
              </>
            )}
          </Button>
        </div>
      </header>

      {(running || progress.length > 0) && (
        <ProgressPanel items={progress} running={running} />
      )}

      {errorMsg && !running && (
        <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {errorMsg}
        </div>
      )}

      {latest && !running && (
        <>
          <BriefViewer brief={latest} />
          <DeckPanel briefId={latest.id} />
        </>
      )}

      {!latest && !running && progress.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-10 text-center text-muted-foreground">
            <FileText className="size-10 text-brand-stone" aria-hidden />
            <p className="text-sm">No brief yet. Click Generate brief to run the agent.</p>
          </CardContent>
        </Card>
      )}
    </section>
  );
}

function ProgressPanel({
  items,
  running,
}: {
  items: ProgressItem[];
  running: boolean;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-sm uppercase tracking-wide text-muted-foreground">
          {running ? (
            <Loader2 className="size-4 animate-spin" aria-hidden />
          ) : (
            <CheckCircle2 className="size-4 text-emerald-600" aria-hidden />
          )}
          Pipeline progress
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ol className="flex flex-col gap-2">
          {items.map((it, i) => (
            <li key={i} className="flex items-center gap-2 text-sm">
              <Icon kind={it.kind} />
              <span className="text-brand-slate">{it.message}</span>
              <Badge variant="muted" className="ml-auto text-[10px]">
                {it.kind}
              </Badge>
            </li>
          ))}
        </ol>
      </CardContent>
    </Card>
  );
}

function Icon({ kind }: { kind: BriefProgressEvent["kind"] }) {
  const cls = cn("size-3.5 shrink-0");
  if (kind === "error") return <XCircle className={cn(cls, "text-red-500")} aria-hidden />;
  if (kind === "done" || kind === "persisted")
    return <CheckCircle2 className={cn(cls, "text-emerald-600")} aria-hidden />;
  return <Loader2 className={cn(cls, "text-brand-accent")} aria-hidden />;
}
