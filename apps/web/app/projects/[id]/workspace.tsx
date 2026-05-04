"use client";

import { useState } from "react";

import { DocumentList } from "@/components/documents/document-list";
import { RetrievalDebug } from "@/components/retrieval/retrieval-debug";
import { DocumentDropzone } from "@/components/upload/document-dropzone";

export function ProjectWorkspace({ projectId }: { projectId: string }) {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="grid gap-10 lg:grid-cols-[1.4fr_1fr]">
      <section className="flex flex-col gap-4">
        <header>
          <h2 className="font-display text-xl font-semibold tracking-tight">
            Source documents
          </h2>
          <p className="text-sm text-muted-foreground">
            Upload .docx and .xlsx files. Ingestion runs automatically and the status
            updates here in real time.
          </p>
        </header>
        <DocumentDropzone
          projectId={projectId}
          onUploaded={() => setRefreshKey((k) => k + 1)}
        />
        <DocumentList projectId={projectId} refreshKey={refreshKey} />
      </section>

      <section className="flex flex-col gap-4">
        <header>
          <h2 className="font-display text-xl font-semibold tracking-tight">
            Retrieval debug
          </h2>
          <p className="text-sm text-muted-foreground">
            Test what the agent will find before generating a brief. Useful for
            sanity-checking that ingestion produced the right chunks.
          </p>
        </header>
        <RetrievalDebug projectId={projectId} />
      </section>
    </div>
  );
}
