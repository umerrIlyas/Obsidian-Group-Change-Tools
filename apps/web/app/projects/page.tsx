import Link from "next/link";
import { ArrowRight, Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ApiError, api } from "@/lib/api-client";

export const dynamic = "force-dynamic";

export default async function ProjectsListPage() {
  let projects: Awaited<ReturnType<typeof api.projects.list>> = [];
  let error: string | null = null;
  try {
    projects = await api.projects.list();
  } catch (e) {
    error = e instanceof ApiError ? e.message : (e as Error).message;
  }

  return (
    <main className="container py-12">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="font-display text-3xl font-semibold tracking-tight">
            Projects
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Each project holds source documents, brand profile, briefs, and decks.
          </p>
        </div>
        <Button asChild>
          <Link href="/projects/new">
            <Plus className="size-4" aria-hidden /> New project
          </Link>
        </Button>
      </div>

      {error && (
        <p className="mb-6 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      )}

      {projects.length === 0 ? (
        <Card>
          <CardHeader className="text-center">
            <CardTitle>No projects yet</CardTitle>
            <CardDescription>
              Create your first project to start uploading change-programme materials.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : (
        <ul className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((p) => (
            <li key={p.id}>
              <Link
                href={`/projects/${p.id}`}
                className="group block rounded-lg border border-brand-hairline bg-card p-5 transition-colors hover:border-brand-accent"
              >
                <div className="flex items-start justify-between gap-2">
                  <h2 className="font-display text-lg font-semibold tracking-tight">
                    {p.name}
                  </h2>
                  <ArrowRight
                    className="size-4 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:text-brand-accent"
                    aria-hidden
                  />
                </div>
                {p.description && (
                  <p className="mt-2 text-sm text-muted-foreground line-clamp-2">
                    {p.description}
                  </p>
                )}
                <p className="mt-4 text-xs text-muted-foreground">
                  Created {new Date(p.created_at).toLocaleDateString()}
                </p>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
