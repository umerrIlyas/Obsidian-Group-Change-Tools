import Link from "next/link";
import { notFound } from "next/navigation";
import { ChevronLeft } from "lucide-react";

import { ProjectWorkspace } from "@/app/projects/[id]/workspace";
import { Button } from "@/components/ui/button";
import { ApiError, api } from "@/lib/api-client";

export const dynamic = "force-dynamic";

export default async function ProjectWorkspacePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  try {
    const project = await api.projects.get(id);
    return (
      <main className="container py-10">
        <div className="mb-6 flex items-center justify-between">
          <Button asChild variant="ghost" size="sm">
            <Link href="/projects">
              <ChevronLeft className="size-4" aria-hidden /> Back to projects
            </Link>
          </Button>
        </div>
        <header className="mb-8 border-b border-brand-hairline pb-6">
          <h1 className="font-display text-3xl font-semibold tracking-tight">
            {project.name}
          </h1>
          {project.description && (
            <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
              {project.description}
            </p>
          )}
        </header>
        <ProjectWorkspace projectId={project.id} />
      </main>
    );
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) {
      notFound();
    }
    throw e;
  }
}
