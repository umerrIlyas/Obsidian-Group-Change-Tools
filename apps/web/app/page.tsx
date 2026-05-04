import Image from "next/image";
import Link from "next/link";
import { ArrowRight, FileText, MessageSquare, Presentation } from "lucide-react";

import { BrandSwatchGrid } from "@/components/brand-swatch";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-background text-foreground">
      <header className="border-b border-brand-hairline">
        <div className="container flex items-center justify-between py-5">
          <div className="flex items-center gap-3">
            <Image
              src="/obsidian-logo.png"
              alt="Obsidian Group"
              width={36}
              height={36}
              priority
            />
            <span className="font-display text-base font-semibold tracking-tight">
              ChangeTools
            </span>
            <span className="hidden text-sm text-muted-foreground md:inline">
              · Obsidian Group MVP
            </span>
          </div>
          <Button asChild variant="ghost" size="sm">
            <Link href="https://github.com">View on GitHub</Link>
          </Button>
        </div>
      </header>

      <section className="container grid gap-12 py-16 md:grid-cols-[1.4fr_1fr] md:py-24">
        <div className="flex flex-col justify-center gap-6">
          <span className="inline-flex w-fit rounded-full border border-brand-hairline bg-brand-fog px-3 py-1 text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Change strategy · powered by RAG
          </span>
          <h1 className="font-display text-4xl font-semibold leading-tight tracking-tight md:text-5xl">
            Turn change-programme noise into a{" "}
            <span className="text-brand-accent">structured brief</span> and a
            branded deck.
          </h1>
          <p className="max-w-xl text-base leading-relaxed text-muted-foreground md:text-lg">
            Upload your call notes, KPI data, and stakeholder feedback. The agent
            grounds every claim in your source material, surfaces conflicts
            instead of hiding them, and renders a slide deck that already looks
            like yours.
          </p>
          <div className="flex flex-col gap-3 sm:flex-row">
            <Button asChild size="lg">
              <Link href="/projects/new">
                New project <ArrowRight className="size-4" aria-hidden />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link href="#how-it-works">How it works</Link>
            </Button>
          </div>
        </div>

        <div className="relative flex items-center justify-center">
          <div className="absolute inset-0 -z-10 rounded-2xl bg-gradient-to-br from-brand-fog to-transparent" />
          <Image
            src="/obsidian-logo.png"
            alt="Obsidian Group logo"
            width={260}
            height={260}
            className="drop-shadow-sm"
          />
        </div>
      </section>

      <section id="how-it-works" className="border-y border-brand-hairline bg-brand-fog/40">
        <div className="container grid gap-6 py-16 md:grid-cols-3">
          <Card>
            <CardHeader>
              <FileText className="size-6 text-brand-accent" aria-hidden />
              <CardTitle>1. Ingest source material</CardTitle>
              <CardDescription>
                Drop in call notes, change data packs, and brand assets. We parse
                docx, xlsx, and images, chunk them, and embed them locally.
              </CardDescription>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <Presentation className="size-6 text-brand-accent" aria-hidden />
              <CardTitle>2. Generate brief + deck</CardTitle>
              <CardDescription>
                A LangGraph agent drafts each section in parallel, validates
                citations, and surfaces cross-source conflicts before rendering
                the brief and a branded .pptx.
              </CardDescription>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <MessageSquare className="size-6 text-brand-accent" aria-hidden />
              <CardTitle>3. Refine in chat</CardTitle>
              <CardDescription>
                Sharpen risk language, regenerate slides, or ask questions about
                your source material — every change is versioned and traced in
                LangSmith.
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </section>

      <section className="container py-16">
        <div className="mb-8 max-w-2xl">
          <h2 className="font-display text-2xl font-semibold tracking-tight md:text-3xl">
            Pre-themed for Obsidian Group
          </h2>
          <p className="mt-2 text-muted-foreground">
            The default brand profile uses Obsidian Group&apos;s palette and
            type system. Upload your own logo and colours to re-theme the app
            and generated outputs.
          </p>
        </div>
        <BrandSwatchGrid />
      </section>

      <footer className="border-t border-brand-hairline">
        <div className="container py-8 text-sm text-muted-foreground">
          ChangeTools MVP · for Obsidian Group technical assessment ·{" "}
          <Link href="/health" className="text-brand-accent hover:underline">
            API health
          </Link>
        </div>
      </footer>
    </main>
  );
}
