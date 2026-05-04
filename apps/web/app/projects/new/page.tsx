import Link from "next/link";

import { Button } from "@/components/ui/button";

/**
 * Placeholder — Phase 2 introduces the real upload flow.
 */
export default function NewProjectPage() {
  return (
    <main className="container flex min-h-screen flex-col items-center justify-center gap-6 text-center">
      <h1 className="font-display text-3xl font-semibold tracking-tight">
        New project — coming in Phase 2
      </h1>
      <p className="max-w-md text-muted-foreground">
        The upload flow lands in the next phase. For now you can confirm the
        backend is reachable and the brand palette is wired correctly.
      </p>
      <div className="flex gap-3">
        <Button asChild>
          <Link href="/">Back home</Link>
        </Button>
        <Button asChild variant="outline">
          <Link href="/health">API health</Link>
        </Button>
      </div>
    </main>
  );
}
