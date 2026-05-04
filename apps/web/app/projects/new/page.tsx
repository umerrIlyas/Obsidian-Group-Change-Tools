"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, api } from "@/lib/api-client";

export default function NewProjectPage() {
  const router = useRouter();
  const [name, setName] = useState("Obsidian Group transformation");
  const [description, setDescription] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setPending(true);
    setError(null);
    try {
      const project = await api.projects.create({
        name: name.trim(),
        description: description.trim() || null,
      });
      router.push(`/projects/${project.id}`);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : (e as Error).message);
      setPending(false);
    }
  }

  return (
    <main className="container max-w-xl py-16">
      <h1 className="font-display text-3xl font-semibold tracking-tight">
        New project
      </h1>
      <p className="mt-2 text-sm text-muted-foreground">
        A project groups source documents, your brand profile, generated briefs, and decks.
      </p>

      <form onSubmit={onSubmit} className="mt-8 flex flex-col gap-5">
        <div className="flex flex-col gap-2">
          <Label htmlFor="name">Name</Label>
          <Input
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            maxLength={200}
          />
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="description">Description (optional)</Label>
          <Textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What change programme is this for?"
            rows={3}
            maxLength={2000}
          />
        </div>

        {error && (
          <p className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </p>
        )}

        <div className="flex items-center gap-2">
          <Button type="submit" disabled={pending || !name.trim()}>
            {pending ? "Creating…" : "Create project"}
          </Button>
          <Button asChild variant="ghost">
            <Link href="/projects">Cancel</Link>
          </Button>
        </div>
      </form>
    </main>
  );
}
