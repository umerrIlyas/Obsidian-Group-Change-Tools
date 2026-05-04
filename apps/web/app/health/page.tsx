import Link from "next/link";

import { Button } from "@/components/ui/button";
import { api, ApiError } from "@/lib/api-client";

export const dynamic = "force-dynamic";

export default async function HealthPage() {
  let health: Awaited<ReturnType<typeof api.health>> | null = null;
  let error: string | null = null;
  try {
    health = await api.health();
  } catch (e) {
    error = e instanceof ApiError ? `${e.status} ${e.message}` : (e as Error).message;
  }

  return (
    <main className="container py-16">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="font-display text-2xl font-semibold tracking-tight">
          Backend health
        </h1>
        <Button asChild variant="outline" size="sm">
          <Link href="/">Home</Link>
        </Button>
      </div>

      {error ? (
        <pre className="rounded-md border border-red-300 bg-red-50 p-4 text-sm text-red-900">
          Could not reach backend: {error}
          {"\n\n"}
          Check that NEXT_PUBLIC_API_URL is set and the FastAPI server is running.
        </pre>
      ) : health ? (
        <dl className="grid gap-4 rounded-md border border-brand-hairline p-6 sm:grid-cols-2">
          {Object.entries(health).map(([key, value]) => (
            <div key={key}>
              <dt className="text-xs uppercase tracking-wide text-muted-foreground">
                {key}
              </dt>
              <dd className="font-mono text-sm">{String(value)}</dd>
            </div>
          ))}
        </dl>
      ) : null}
    </main>
  );
}
