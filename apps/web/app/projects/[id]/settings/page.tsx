import Link from "next/link";
import { notFound } from "next/navigation";
import { ChevronLeft } from "lucide-react";

import { BrandForm } from "@/components/brand/brand-form";
import { Button } from "@/components/ui/button";
import { ApiError, api } from "@/lib/api-client";

export const dynamic = "force-dynamic";

export default async function BrandSettingsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  let project: Awaited<ReturnType<typeof api.projects.get>>;
  try {
    project = await api.projects.get(id);
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) notFound();
    throw e;
  }
  const profile = await api.brand.get(id);

  return (
    <main className="container max-w-3xl py-10">
      <div className="mb-6">
        <Button asChild variant="ghost" size="sm">
          <Link href={`/projects/${id}`}>
            <ChevronLeft className="size-4" aria-hidden /> Back to workspace
          </Link>
        </Button>
      </div>

      <header className="mb-8 border-b border-brand-hairline pb-6">
        <h1 className="font-display text-3xl font-semibold tracking-tight">
          Brand settings
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          {project.name} — palette, fonts, and logo. These drive both the workspace UI
          and the generated slide deck.
        </p>
      </header>

      <BrandForm projectId={id} initialProfile={profile} />
    </main>
  );
}
