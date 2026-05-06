"use client";

import { Download, FileType2, Loader2, Presentation } from "lucide-react";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ApiError,
  type Deck,
  api,
  backendUrl,
} from "@/lib/api-client";

type Props = {
  briefId: string;
};

/**
 * Generate / preview / download the slide deck for a brief.
 *
 * The PDF preview is a plain ``<iframe>`` pointing at the backend's PDF
 * endpoint — modern browsers render PDFs natively, no need to bundle PDF.js.
 * If LibreOffice is missing in the deploy environment the deck still
 * generates as .pptx; we hide the preview and surface a hint.
 */
export function DeckPanel({ briefId }: Props) {
  const [deck, setDeck] = useState<Deck | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const latest = await api.decks.latestForBrief(briefId);
        if (!cancelled) setDeck(latest);
      } catch (e) {
        if (e instanceof ApiError && e.status !== 404) setError(e.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [briefId]);

  async function onGenerate() {
    setGenerating(true);
    setError(null);
    try {
      const fresh = await api.decks.generate(briefId);
      setDeck(fresh);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Deck generation failed");
    } finally {
      setGenerating(false);
    }
  }

  if (loading) return null;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle>Slide deck</CardTitle>
          <p className="mt-1 text-sm text-muted-foreground">
            One-click branded .pptx export of this brief, with a per-slide
            sources footer.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {deck && (
            <Badge variant="muted">
              {deck.slide_count} slide{deck.slide_count === 1 ? "" : "s"}
            </Badge>
          )}
          <Button onClick={onGenerate} disabled={generating}>
            {generating ? (
              <>
                <Loader2 className="size-4 animate-spin" aria-hidden /> Rendering…
              </>
            ) : (
              <>
                <Presentation className="size-4" aria-hidden />
                {deck ? "Regenerate deck" : "Generate deck"}
              </>
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {error && (
          <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {deck?.status === "failed" && (
          <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            Last render failed: {deck.error ?? "unknown error"}
          </div>
        )}

        {deck?.status === "ready" && (
          <>
            <div className="flex flex-wrap items-center gap-2">
              {deck.pptx_url && (
                <Button asChild variant="outline" size="sm">
                  <a href={backendUrl(deck.pptx_url)} download>
                    <Download className="size-4" aria-hidden /> Download .pptx
                  </a>
                </Button>
              )}
              {deck.pdf_url ? (
                <Button asChild variant="ghost" size="sm">
                  <a
                    href={backendUrl(deck.pdf_url)}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <FileType2 className="size-4" aria-hidden /> Open PDF in new tab
                  </a>
                </Button>
              ) : (
                <span className="text-xs text-muted-foreground">
                  PDF preview unavailable (LibreOffice not installed in this env).
                </span>
              )}
            </div>

            {deck.pdf_url && (
              <div className="overflow-hidden rounded-md border border-brand-hairline bg-white">
                <iframe
                  key={deck.id}
                  src={backendUrl(deck.pdf_url)}
                  title="Deck PDF preview"
                  className="h-[640px] w-full"
                />
              </div>
            )}
          </>
        )}

        {!deck && !generating && (
          <p className="text-sm text-muted-foreground">
            No deck yet. Click Generate to render a branded .pptx for this brief.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
