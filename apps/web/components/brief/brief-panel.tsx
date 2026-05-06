"use client";

import { CheckCircle2, FileText, Loader2, Sparkles, XCircle } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { BriefViewer } from "@/components/brief/brief-viewer";
import { DeckPanel } from "@/components/brief/deck-panel";
import { BriefVersionSelector } from "@/components/brief/version-selector";
import { ChatPanel } from "@/components/chat/chat-panel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ApiError,
  type Brief,
  type BriefProgressEvent,
  type BriefSummary,
  api,
  streamBriefGeneration,
} from "@/lib/api-client";
import { cn } from "@/lib/utils";

type ProgressItem = {
  kind: BriefProgressEvent["kind"];
  message: string;
  ts: number;
};

type UpdateToast = {
  brief_id: string;
  version: number;
  section: string;
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
  const [versions, setVersions] = useState<BriefSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [latest, setLatest] = useState<Brief | null>(null);
  const [progress, setProgress] = useState<ProgressItem[]>([]);
  const [running, setRunning] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [updateToast, setUpdateToast] = useState<UpdateToast | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const loadVersions = useCallback(
    async (selectId?: string) => {
      try {
        const list = await api.briefs.list(projectId);
        setVersions(list);
        if (list.length === 0) {
          setSelectedId(null);
          setLatest(null);
          return;
        }
        const target = selectId ?? list[0].id;
        setSelectedId(target);
        const brief = await api.briefs.get(target);
        setLatest(brief);
      } catch (e) {
        if (e instanceof ApiError && e.status !== 404) {
          setErrorMsg(e.message);
        }
      }
    },
    [projectId],
  );

  useEffect(() => {
    void loadVersions();
  }, [loadVersions]);

  async function onSelectVersion(briefId: string) {
    setSelectedId(briefId);
    try {
      const brief = await api.briefs.get(briefId);
      setLatest(brief);
    } catch (e) {
      if (e instanceof ApiError) setErrorMsg(e.message);
    }
  }

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
        setProgress((prev) => [
          ...prev,
          { kind: ev.kind, message, ts: Date.now() },
        ]);
        if (ev.brief_id) briefId = ev.brief_id;
        if (ev.kind === "error") setErrorMsg(message);
      }
      if (briefId) await loadVersions(briefId);
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

  // Called from <ChatPanel> when the agent updated a brief section.
  const onChatBriefUpdated = useCallback(
    (detail: UpdateToast) => {
      setUpdateToast(detail);
      void loadVersions(detail.brief_id);
    },
    [loadVersions],
  );

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
          {versions.length > 0 && (
            <BriefVersionSelector
              versions={versions}
              selectedId={selectedId}
              onSelect={onSelectVersion}
            />
          )}
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

      {updateToast && (
        <div className="flex items-center justify-between gap-3 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm text-emerald-800">
          <span>
            Brief updated to <strong>v{updateToast.version}</strong> —{" "}
            <span className="font-mono">{updateToast.section}</span> revised.
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => onSelectVersion(updateToast.brief_id)}
              className="font-medium underline"
            >
              View
            </button>
            <button
              type="button"
              onClick={() => setUpdateToast(null)}
              className="text-emerald-600"
              aria-label="Dismiss"
            >
              ✕
            </button>
          </div>
        </div>
      )}

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
          <ChatPanel projectId={projectId} onBriefUpdated={onChatBriefUpdated} />
        </>
      )}

      {!latest && !running && progress.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-10 text-center text-muted-foreground">
            <FileText className="size-10 text-brand-stone" aria-hidden />
            <p className="text-sm">
              No brief yet. Click Generate brief to run the agent.
            </p>
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
  if (kind === "error")
    return <XCircle className={cn(cls, "text-red-500")} aria-hidden />;
  if (kind === "done" || kind === "persisted")
    return <CheckCircle2 className={cn(cls, "text-emerald-600")} aria-hidden />;
  return <Loader2 className={cn(cls, "text-brand-accent")} aria-hidden />;
}
