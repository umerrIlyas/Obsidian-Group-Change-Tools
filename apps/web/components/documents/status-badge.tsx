import { Loader2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { DocumentStatus } from "@/lib/api-client";

const LABEL: Record<DocumentStatus, string> = {
  uploaded: "Uploaded",
  parsing: "Parsing",
  chunking: "Chunking",
  embedding: "Embedding",
  ready: "Ready",
  failed: "Failed",
};

export function DocumentStatusBadge({ status }: { status: DocumentStatus }) {
  if (status === "ready") {
    return <Badge variant="success">Ready</Badge>;
  }
  if (status === "failed") {
    return <Badge variant="danger">Failed</Badge>;
  }
  return (
    <Badge variant="accent">
      <Loader2 className="size-3 animate-spin" aria-hidden />
      {LABEL[status]}
    </Badge>
  );
}
