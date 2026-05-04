"use client";

import { Search } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ApiError, api, type RetrievedHit } from "@/lib/api-client";

type Props = {
  projectId: string;
};

export function RetrievalDebug({ projectId }: Props) {
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<RetrievedHit[] | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setPending(true);
    setError(null);
    try {
      const response = await api.retrieval.query(projectId, { query, top_k: 8 });
      setHits(response.hits);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : (e as Error).message);
      setHits(null);
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="flex flex-col gap-4">
      <form onSubmit={onSubmit} className="flex items-center gap-2">
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. middle management resistance"
          aria-label="Retrieval query"
        />
        <Button type="submit" disabled={pending || !query.trim()}>
          <Search className="size-4" aria-hidden />
          {pending ? "Searching" : "Search"}
        </Button>
      </form>

      {error && (
        <p className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      )}

      {hits && hits.length === 0 && (
        <p className="text-sm text-muted-foreground">
          No matches yet. Make sure documents have finished ingesting.
        </p>
      )}

      {hits && hits.length > 0 && (
        <ol className="flex flex-col gap-3">
          {hits.map((hit, i) => (
            <li
              key={hit.chunk_id}
              className="rounded-md border border-brand-hairline bg-card p-4"
            >
              <div className="mb-2 flex items-center justify-between gap-2 text-xs">
                <span className="text-muted-foreground">
                  {i + 1}. {hit.document_filename}{" "}
                  <span className="rounded bg-brand-fog px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wide">
                    {hit.document_kind}
                  </span>
                </span>
                <span className="font-mono text-brand-accent">
                  score {hit.score.toFixed(3)}
                </span>
              </div>
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground">
                {hit.text}
              </p>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
