"use client";

import { Loader2, Send, Sparkles } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { ToolCallCard } from "@/components/chat/tool-call-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  api,
  type ChatMessage,
  type ChatStreamEvent,
  streamChatMessage,
} from "@/lib/api-client";
import { cn } from "@/lib/utils";

type Props = {
  projectId: string;
  onBriefUpdated?: (detail: {
    brief_id: string;
    version: number;
    section: string;
  }) => void;
};

type LiveTool = {
  id: string;
  name: string;
  args: Record<string, unknown>;
  output: string | null;
  status: "running" | "done";
};

type LiveTurn = {
  text: string;
  tools: LiveTool[];
  done: boolean;
};

export function ChatPanel({ projectId, onBriefUpdated }: Props) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [live, setLive] = useState<LiveTurn | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Load latest session on mount.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const sessions = await api.chat.listSessions(projectId);
        if (cancelled) return;
        if (sessions.length === 0) return;
        const latest = sessions[0];
        setSessionId(latest.id);
        const messages = await api.chat.listMessages(projectId, latest.id);
        if (!cancelled) setHistory(messages);
      } catch {
        // 404 / network errors — start fresh
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  // Auto-scroll to bottom whenever the conversation changes.
  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [history, live]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || pending) return;

    setError(null);
    setPending(true);
    setInput("");
    setLive({ text: "", tools: [], done: false });

    const abort = new AbortController();
    abortRef.current = abort;

    try {
      for await (const ev of streamChatMessage(
        projectId,
        { message: text, session_id: sessionId ?? undefined },
        abort.signal,
      )) {
        applyEvent(ev);
      }
      // Finalize: pull fresh history (includes the assistant + tool messages).
      const sid = sessionId;
      if (sid) {
        const fresh = await api.chat.listMessages(projectId, sid);
        setHistory(fresh);
      }
      setLive(null);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Chat failed";
      setError(msg);
    } finally {
      setPending(false);
      abortRef.current = null;
    }
  }

  function applyEvent(ev: ChatStreamEvent) {
    if (ev.kind === "session") {
      setSessionId(ev.session_id);
      return;
    }
    if (ev.kind === "token") {
      setLive((prev) =>
        prev ? { ...prev, text: prev.text + ev.text } : prev,
      );
      return;
    }
    if (ev.kind === "tool_start") {
      setLive((prev) =>
        prev
          ? {
              ...prev,
              tools: [
                ...prev.tools,
                {
                  id: ev.id,
                  name: ev.name,
                  args: ev.args,
                  output: null,
                  status: "running",
                },
              ],
            }
          : prev,
      );
      return;
    }
    if (ev.kind === "tool_end") {
      setLive((prev) =>
        prev
          ? {
              ...prev,
              tools: prev.tools.map((t) =>
                t.id === ev.id
                  ? { ...t, output: ev.output, status: "done" as const }
                  : t,
              ),
            }
          : prev,
      );
      return;
    }
    if (ev.kind === "brief_updated") {
      onBriefUpdated?.(ev);
      return;
    }
    if (ev.kind === "error") {
      setError(ev.message);
      return;
    }
    if (ev.kind === "final") {
      setLive((prev) => (prev ? { ...prev, done: true } : prev));
    }
  }

  function onCancel() {
    abortRef.current?.abort();
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="size-4 text-brand-accent" aria-hidden />
            Refine with chat
          </CardTitle>
          <p className="mt-1 text-sm text-muted-foreground">
            Ask the agent to tighten sections, surface gaps, or add new evidence.
            It writes a new brief version and refreshes the deck.
          </p>
        </div>
        {pending && (
          <Button variant="outline" size="sm" onClick={onCancel}>
            Cancel
          </Button>
        )}
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div
          ref={scrollRef}
          className={cn(
            "flex max-h-[480px] flex-col gap-3 overflow-y-auto rounded-md border border-brand-hairline bg-brand-fog/30 p-4",
            "scroll-smooth",
          )}
        >
          {history.length === 0 && live === null && (
            <p className="text-center text-sm text-muted-foreground">
              No messages yet. Try: <em>“Tighten the executive summary to two
              sentences.”</em>
            </p>
          )}

          {history.map((m) => (
            <PersistedMessage key={m.id} message={m} />
          ))}

          {live && <LiveBubble live={live} />}
        </div>

        {error && (
          <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <form onSubmit={onSubmit} className="flex items-center gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask the refinement agent…"
            disabled={pending}
          />
          <Button type="submit" disabled={pending || !input.trim()}>
            {pending ? (
              <Loader2 className="size-4 animate-spin" aria-hidden />
            ) : (
              <Send className="size-4" aria-hidden />
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function PersistedMessage({ message }: { message: ChatMessage }) {
  if (message.role === "tool") {
    return (
      <ToolCallCard
        name={message.tool_name ?? "tool"}
        args={(message.meta?.args as Record<string, unknown>) ?? {}}
        output={message.content}
        status="done"
      />
    );
  }
  if (message.role === "user") {
    return <UserBubble text={message.content} />;
  }
  return (
    <AssistantBubble
      text={message.content}
      tools={message.tool_calls.map((tc) => ({
        id: tc.id,
        name: tc.name,
        args: tc.args,
        output: null,
        status: "done" as const,
      }))}
    />
  );
}

function UserBubble({ text }: { text: string }) {
  return (
    <div className="ml-auto max-w-[85%] rounded-lg bg-brand-obsidian px-3 py-2 text-sm text-white">
      {text}
    </div>
  );
}

function AssistantBubble({
  text,
  tools,
}: {
  text: string;
  tools: LiveTool[];
}) {
  return (
    <div className="mr-auto flex max-w-[85%] flex-col gap-2">
      {tools.length > 0 && (
        <div className="flex flex-col gap-1">
          {tools.map((t) => (
            <ToolCallCard
              key={t.id}
              name={t.name}
              args={t.args}
              output={t.output}
              status={t.status}
            />
          ))}
        </div>
      )}
      {text && (
        <div className="rounded-lg border border-brand-hairline bg-white px-3 py-2 text-sm text-brand-slate">
          {text}
        </div>
      )}
    </div>
  );
}

function LiveBubble({ live }: { live: LiveTurn }) {
  return (
    <div className="mr-auto flex max-w-[85%] flex-col gap-2">
      {live.tools.length > 0 && (
        <div className="flex flex-col gap-1">
          {live.tools.map((t) => (
            <ToolCallCard
              key={t.id}
              name={t.name}
              args={t.args}
              output={t.output}
              status={t.status}
            />
          ))}
        </div>
      )}
      <div className="flex items-center gap-2 rounded-lg border border-brand-hairline bg-white px-3 py-2 text-sm text-brand-slate">
        {live.text || (
          <span className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="size-3 animate-spin" aria-hidden /> thinking…
          </span>
        )}
        {!live.done && live.text && (
          <Badge variant="muted" className="ml-auto text-[10px]">
            streaming
          </Badge>
        )}
      </div>
    </div>
  );
}
