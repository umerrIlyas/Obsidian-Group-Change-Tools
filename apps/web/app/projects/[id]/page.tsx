import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ChevronLeft, Settings } from "lucide-react";

import { ProjectWorkspace } from "@/app/projects/[id]/workspace";
import { BrandVars } from "@/components/brand/brand-vars";
import { Button } from "@/components/ui/button";
import { ApiError, api, backendUrl } from "@/lib/api-client";

export const dynamic = "force-dynamic";

export default async function ProjectWorkspacePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  try {
    const [project, brandProfile] = await Promise.all([
      api.projects.get(id),
      api.brand.get(id),
    ]);

    return (
      <BrandVars profile={brandProfile}>
        <main className="container py-10">
          <div className="mb-6 flex items-center justify-between">
            <Button asChild variant="ghost" size="sm">
              <Link href="/projects">
                <ChevronLeft className="size-4" aria-hidden /> Back to projects
              </Link>
            </Button>
            <Button asChild variant="outline" size="sm">
              <Link href={`/projects/${id}/settings`}>
                <Settings className="size-4" aria-hidden /> Brand settings
              </Link>
            </Button>
          </div>
          <header className="mb-8 flex items-start justify-between gap-6 border-b border-brand-hairline pb-6">
            <div>
              <h1 className="font-display text-3xl font-semibold tracking-tight">
                {project.name}
              </h1>
              {project.description && (
                <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
                  {project.description}
                </p>
              )}
              {!brandProfile && (
                <p className="mt-3 text-xs text-muted-foreground">
                  No brand profile yet —{" "}
                  <Link
                    href={`/projects/${id}/settings`}
                    className="text-brand-accent underline"
                  >
                    set one up
                  </Link>{" "}
                  so the deck renders with your branding.
                </p>
              )}
            </div>
            {brandProfile?.logo_url && (
              <Image
                src={backendUrl(brandProfile.logo_url)}
                alt="Project logo"
                width={64}
                height={64}
                className="rounded border border-brand-hairline bg-white p-1"
                unoptimized
              />
            )}
          </header>
          <ProjectWorkspace projectId={project.id} />
        </main>
      </BrandVars>
    );
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) {
      notFound();
    }
    throw e;
  }
}
