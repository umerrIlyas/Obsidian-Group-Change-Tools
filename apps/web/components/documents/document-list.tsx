"use client";

import { FileSpreadsheet, FileText, FileX } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { DocumentStatusBadge } from "@/components/documents/status-badge";
import { ApiError, api, type DocumentSummary } from "@/lib/api-client";

type Props = {
  projectId: string;
  refreshKey?: number;
};

const ICONS: Record<string, typeof FileText> = {
  docx: FileText,
  xlsx: FileSpreadsheet,
  pdf: FileText,
  image: FileText,
  other: FileText,
};

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

export function DocumentList({ projectId, refreshKey = 0 }: Props) {
  const [docs, setDocs] = useState<DocumentSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  const fetchDocs = useCallback(async () => {
    try {
      setDocs(await api.documents.listByProject(projectId));
      setError(null);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : (e as Error).message);
    }
  }, [projectId]);

  useEffect(() => {
    void fetchDocs();
  }, [fetchDocs, refreshKey]);

  // Poll while any document is mid-pipeline.
  useEffect(() => {
    const inFlight = docs.some((d) => d.status !== "ready" && d.status !== "failed");
    if (!inFlight) return;
    const id = setInterval(fetchDocs, 2000);
    return () => clearInterval(id);
  }, [docs, fetchDocs]);

  if (error) {
    return (
      <p className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
        Could not load documents: {error}
      </p>
    );
  }

  if (!docs.length) {
    return (
      <p className="rounded-md border border-dashed border-brand-hairline bg-brand-fog/40 p-6 text-center text-sm text-muted-foreground">
        No documents yet. Drop a file above to start.
      </p>
    );
  }

  return (
    <ul className="divide-y divide-brand-hairline rounded-lg border border-brand-hairline">
      {docs.map((doc) => {
        const Icon = ICONS[doc.kind] ?? FileX;
        return (
          <li key={doc.id} className="flex items-center gap-4 px-4 py-3">
            <Icon className="size-5 shrink-0 text-brand-accent" aria-hidden />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{doc.filename}</p>
              <p className="text-xs text-muted-foreground">
                {doc.kind} · {formatBytes(doc.size_bytes)}
              </p>
              {doc.error && (
                <p className="mt-1 truncate text-xs text-red-600">{doc.error}</p>
              )}
            </div>
            <DocumentStatusBadge status={doc.status} />
          </li>
        );
      })}
    </ul>
  );
}
