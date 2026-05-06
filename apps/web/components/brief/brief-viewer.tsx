import { AlertTriangle } from "lucide-react";

import { CitationChips } from "@/components/brief/citation-chip";
import { ConfidenceBadge } from "@/components/brief/confidence-badge";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type {
  Brief,
  BriefConflict,
  BriefKPI,
  BriefRecommendation,
  BriefRisk,
  BriefStakeholder,
  BriefTheme,
  Priority,
  RiskSeverity,
  StakeholderSentiment,
} from "@/lib/api-client";
import { cn } from "@/lib/utils";

const SEVERITY_VARIANT: Record<RiskSeverity, "muted" | "warning" | "danger"> = {
  low: "muted",
  medium: "warning",
  high: "danger",
  critical: "danger",
};

const SENTIMENT_VARIANT: Record<
  StakeholderSentiment,
  "success" | "muted" | "warning" | "danger"
> = {
  positive: "success",
  neutral: "muted",
  concerned: "warning",
  resistant: "danger",
};

const PRIORITY_VARIANT: Record<Priority, "danger" | "warning" | "accent" | "muted"> = {
  P0: "danger",
  P1: "warning",
  P2: "accent",
  P3: "muted",
};

export function BriefViewer({ brief }: { brief: Brief }) {
  const c = brief.content;
  return (
    <div className="flex flex-col gap-6">
      <ExecutiveSummarySection summary={c.executive_summary} />
      {c.conflicts.length > 0 && <ConflictsSection conflicts={c.conflicts} />}
      <ThemesSection themes={c.themes} />
      <KPIsSection kpis={c.kpis} />
      <RisksSection risks={c.risks} />
      <StakeholdersSection stakeholders={c.stakeholders} />
      <RecommendationsSection recommendations={c.recommendations} />
      <BriefMetrics brief={brief} />
    </div>
  );
}

function SectionCard({
  title,
  count,
  children,
}: {
  title: string;
  count?: number;
  children: React.ReactNode;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle>{title}</CardTitle>
        {count !== undefined && (
          <Badge variant="muted">
            {count} item{count === 1 ? "" : "s"}
          </Badge>
        )}
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

function ExecutiveSummarySection({
  summary,
}: {
  summary: Brief["content"]["executive_summary"];
}) {
  return (
    <Card className="border-brand-accent/30">
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div>
            <Badge variant="accent" className="mb-2">
              Executive summary
            </Badge>
            <CardTitle className="text-2xl">{summary.headline}</CardTitle>
          </div>
          <ConfidenceBadge confidence={summary.confidence} />
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <p className="leading-relaxed text-brand-slate">{summary.body}</p>
        <CitationChips refs={summary.evidence} />
      </CardContent>
    </Card>
  );
}

function ConflictsSection({ conflicts }: { conflicts: BriefConflict[] }) {
  return (
    <Card className="border-amber-200 bg-amber-50/40">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-amber-900">
          <AlertTriangle className="size-5" aria-hidden />
          Source conflicts ({conflicts.length})
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {conflicts.map((c, i) => (
          <div
            key={`${c.topic}-${i}`}
            className="rounded-md border border-amber-200 bg-white p-4"
          >
            <h4 className="font-medium text-brand-obsidian">{c.topic}</h4>
            <div className="mt-2 grid gap-3 md:grid-cols-2">
              <div>
                <span className="text-xs font-semibold uppercase tracking-wide text-amber-700">
                  Position A (call notes)
                </span>
                <p className="mt-1 text-sm text-brand-slate">{c.position_a}</p>
                <CitationChips refs={c.sources_a} className="mt-1" />
              </div>
              <div>
                <span className="text-xs font-semibold uppercase tracking-wide text-amber-700">
                  Position B (data pack)
                </span>
                <p className="mt-1 text-sm text-brand-slate">{c.position_b}</p>
                <CitationChips refs={c.sources_b} className="mt-1" />
              </div>
            </div>
            {c.suggested_resolution && (
              <p className="mt-3 rounded bg-amber-100/60 p-2 text-xs text-amber-900">
                <span className="font-semibold">Suggested resolution: </span>
                {c.suggested_resolution}
              </p>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function ThemesSection({ themes }: { themes: BriefTheme[] }) {
  if (themes.length === 0) return null;
  return (
    <SectionCard title="Themes" count={themes.length}>
      <ul className="flex flex-col gap-3">
        {themes.map((t, i) => (
          <li
            key={`${t.title}-${i}`}
            className="rounded-md border border-brand-hairline bg-brand-fog/30 p-3"
          >
            <div className="flex items-start justify-between gap-3">
              <h4 className="font-medium text-brand-obsidian">{t.title}</h4>
              <ConfidenceBadge confidence={t.confidence} />
            </div>
            <p className="mt-1 text-sm leading-relaxed text-brand-slate">
              {t.description}
            </p>
            <CitationChips refs={t.evidence} className="mt-2" />
          </li>
        ))}
      </ul>
    </SectionCard>
  );
}

function KPIsSection({ kpis }: { kpis: BriefKPI[] }) {
  if (kpis.length === 0) return null;
  return (
    <SectionCard title="KPIs" count={kpis.length}>
      <div className="grid gap-3 md:grid-cols-2">
        {kpis.map((k, i) => (
          <div
            key={`${k.name}-${i}`}
            className="rounded-md border border-brand-hairline bg-white p-3"
          >
            <div className="flex items-start justify-between gap-2">
              <h4 className="font-medium text-brand-obsidian">{k.name}</h4>
              <ConfidenceBadge confidence={k.confidence} />
            </div>
            <div className="mt-2 flex flex-wrap items-baseline gap-3 text-sm">
              <span className="font-display text-2xl font-semibold text-brand-obsidian">
                {k.current_value}
              </span>
              {k.target_value && (
                <span className="text-xs text-muted-foreground">
                  Target: {k.target_value}
                </span>
              )}
              {k.trend && (
                <span className="text-xs text-muted-foreground">
                  Trend: {k.trend}
                </span>
              )}
            </div>
            {k.gap && (
              <p className="mt-1 text-xs text-brand-slate">Gap: {k.gap}</p>
            )}
            <CitationChips refs={k.evidence} className="mt-2" />
          </div>
        ))}
      </div>
    </SectionCard>
  );
}

function RisksSection({ risks }: { risks: BriefRisk[] }) {
  if (risks.length === 0) return null;
  return (
    <SectionCard title="Risks" count={risks.length}>
      <ul className="flex flex-col gap-3">
        {risks.map((r) => (
          <li
            key={r.risk_id}
            className="rounded-md border border-brand-hairline p-3"
          >
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="default">{r.risk_id}</Badge>
              <Badge variant={SEVERITY_VARIANT[r.severity]}>
                {r.severity} severity
              </Badge>
              <ConfidenceBadge confidence={r.confidence} />
              <span className="ml-auto text-xs text-muted-foreground">
                {r.owner ?? "no owner"}
              </span>
            </div>
            <h4 className="mt-2 font-medium text-brand-obsidian">{r.title}</h4>
            <p className="mt-1 text-sm leading-relaxed text-brand-slate">
              {r.description}
            </p>
            {r.mitigation && (
              <p className="mt-2 rounded bg-brand-fog/40 p-2 text-xs text-brand-slate">
                <span className="font-semibold">Mitigation: </span>
                {r.mitigation}
              </p>
            )}
            <CitationChips refs={r.evidence} className="mt-2" />
          </li>
        ))}
      </ul>
    </SectionCard>
  );
}

function StakeholdersSection({
  stakeholders,
}: {
  stakeholders: BriefStakeholder[];
}) {
  if (stakeholders.length === 0) return null;
  return (
    <SectionCard title="Stakeholders" count={stakeholders.length}>
      <ul className="grid gap-3 md:grid-cols-2">
        {stakeholders.map((s, i) => (
          <li
            key={`${s.name}-${i}`}
            className="rounded-md border border-brand-hairline p-3"
          >
            <div className="flex items-center justify-between gap-2">
              <div>
                <h4 className="font-medium text-brand-obsidian">{s.name}</h4>
                <p className="text-xs text-muted-foreground">{s.role}</p>
              </div>
              <Badge variant={SENTIMENT_VARIANT[s.sentiment]}>{s.sentiment}</Badge>
            </div>
            <p className="mt-2 text-sm leading-relaxed text-brand-slate">
              {s.concern}
            </p>
            <div className="mt-2 flex items-center gap-2">
              <ConfidenceBadge confidence={s.confidence} />
              <CitationChips refs={s.evidence} />
            </div>
          </li>
        ))}
      </ul>
    </SectionCard>
  );
}

function RecommendationsSection({
  recommendations,
}: {
  recommendations: BriefRecommendation[];
}) {
  if (recommendations.length === 0) return null;
  return (
    <SectionCard title="Recommendations" count={recommendations.length}>
      <ol className="flex flex-col gap-3">
        {recommendations.map((r, i) => (
          <li
            key={`${r.title}-${i}`}
            className="rounded-md border border-brand-hairline p-3"
          >
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={PRIORITY_VARIANT[r.priority]}>{r.priority}</Badge>
              {r.addresses_risks.map((rid) => (
                <Badge key={rid} variant="muted">
                  addresses {rid}
                </Badge>
              ))}
              <ConfidenceBadge confidence={r.confidence} />
            </div>
            <h4 className="mt-2 font-medium text-brand-obsidian">{r.title}</h4>
            <p className="mt-1 text-sm leading-relaxed text-brand-slate">
              {r.description}
            </p>
            <CitationChips refs={r.evidence} className="mt-2" />
          </li>
        ))}
      </ol>
    </SectionCard>
  );
}

function BriefMetrics({ brief }: { brief: Brief }) {
  const m = brief.metrics ?? {};
  if (Object.keys(m).length === 0) return null;
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm uppercase tracking-wide text-muted-foreground">
          Generation metrics
        </CardTitle>
      </CardHeader>
      <CardContent>
        <dl
          className={cn(
            "grid gap-4 text-xs",
            "grid-cols-2 md:grid-cols-4",
          )}
        >
          {Object.entries(m).map(([k, v]) => (
            <div key={k} className="flex flex-col">
              <dt className="text-muted-foreground">{k}</dt>
              <dd className="font-mono text-brand-obsidian">{String(v)}</dd>
            </div>
          ))}
          <div className="flex flex-col">
            <dt className="text-muted-foreground">model</dt>
            <dd className="font-mono text-brand-obsidian">
              {brief.provider}/{brief.model_name}
            </dd>
          </div>
          <div className="flex flex-col">
            <dt className="text-muted-foreground">version</dt>
            <dd className="font-mono text-brand-obsidian">v{brief.version}</dd>
          </div>
        </dl>
      </CardContent>
    </Card>
  );
}
