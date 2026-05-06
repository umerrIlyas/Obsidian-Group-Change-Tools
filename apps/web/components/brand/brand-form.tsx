"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Sparkles } from "lucide-react";

import { LogoUploader } from "@/components/brand/logo-uploader";
import { PaletteEditor } from "@/components/brand/palette-editor";
import { Button } from "@/components/ui/button";
import {
  ApiError,
  api,
  type BrandProfile,
  type UpdateBrandPayload,
} from "@/lib/api-client";

const DEFAULT_PAYLOAD: UpdateBrandPayload = {
  primary_color: "#0D171E",
  secondary_color: "#2C343C",
  accent_color: "#3A8C91",
  neutrals: { stone: "#6B7280", hairline: "#D9DEE3", fog: "#EEF1F3" },
  font_heading: "Aptos Display",
  font_body: "Aptos",
};

function profileToPayload(profile: BrandProfile): UpdateBrandPayload {
  return {
    primary_color: profile.primary_color,
    secondary_color: profile.secondary_color,
    accent_color: profile.accent_color,
    neutrals: profile.neutrals,
    font_heading: profile.font_heading,
    font_body: profile.font_body,
  };
}

type Props = {
  projectId: string;
  initialProfile: BrandProfile | null;
};

export function BrandForm({ projectId, initialProfile }: Props) {
  const router = useRouter();
  const [profile, setProfile] = useState<BrandProfile | null>(initialProfile);
  const [payload, setPayload] = useState<UpdateBrandPayload>(
    initialProfile ? profileToPayload(initialProfile) : DEFAULT_PAYLOAD,
  );
  const [logoFile, setLogoFile] = useState<File | null>(null);
  const [pending, setPending] = useState<"save" | "preset" | null>(null);
  const [message, setMessage] = useState<{ kind: "success" | "error"; text: string } | null>(null);

  async function onSave(e: React.FormEvent) {
    e.preventDefault();
    setPending("save");
    setMessage(null);
    try {
      const next = logoFile
        ? await api.brand.updateWithLogo(projectId, payload, logoFile)
        : await api.brand.update(projectId, payload);
      setProfile(next);
      setLogoFile(null);
      setMessage({ kind: "success", text: "Brand profile saved." });
      router.refresh();
    } catch (e) {
      setMessage({
        kind: "error",
        text: e instanceof ApiError ? e.message : (e as Error).message,
      });
    } finally {
      setPending(null);
    }
  }

  async function onApplyPreset() {
    setPending("preset");
    setMessage(null);
    try {
      const next = await api.brand.applyObsidianPreset(projectId);
      setProfile(next);
      setPayload(profileToPayload(next));
      setLogoFile(null);
      setMessage({ kind: "success", text: "Obsidian preset applied." });
      router.refresh();
    } catch (e) {
      setMessage({
        kind: "error",
        text: e instanceof ApiError ? e.message : (e as Error).message,
      });
    } finally {
      setPending(null);
    }
  }

  return (
    <form onSubmit={onSave} className="flex flex-col gap-8">
      <section className="flex items-start justify-between gap-4 rounded-lg border border-brand-hairline bg-brand-fog/30 p-4">
        <div>
          <h3 className="font-display text-sm font-semibold">Quick start</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Apply the Obsidian Group preset (palette + logo + Aptos fonts) and edit
            from there.
          </p>
        </div>
        <Button
          type="button"
          variant="accent"
          onClick={onApplyPreset}
          disabled={pending !== null}
        >
          <Sparkles className="size-4" aria-hidden />
          {pending === "preset" ? "Applying…" : "Use Obsidian preset"}
        </Button>
      </section>

      <section className="flex flex-col gap-3">
        <h3 className="font-display text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Logo
        </h3>
        <LogoUploader
          existingLogoUrl={profile?.logo_url ?? null}
          onFileSelected={setLogoFile}
        />
      </section>

      <PaletteEditor value={payload} onChange={setPayload} />

      {message && (
        <p
          className={
            message.kind === "success"
              ? "rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700"
              : "rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700"
          }
        >
          {message.text}
        </p>
      )}

      <div className="flex items-center gap-2">
        <Button type="submit" disabled={pending !== null}>
          {pending === "save" ? "Saving…" : "Save brand profile"}
        </Button>
      </div>
    </form>
  );
}
