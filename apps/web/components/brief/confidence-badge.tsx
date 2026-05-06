import { Badge } from "@/components/ui/badge";
import type { Confidence } from "@/lib/api-client";

const VARIANT: Record<Confidence, "success" | "muted" | "warning"> = {
  high: "success",
  medium: "muted",
  low: "warning",
};

const LABEL: Record<Confidence, string> = {
  high: "High confidence",
  medium: "Medium confidence",
  low: "Low confidence",
};

export function ConfidenceBadge({ confidence }: { confidence: Confidence }) {
  return <Badge variant={VARIANT[confidence]}>{LABEL[confidence]}</Badge>;
}
