"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { Neutrals, UpdateBrandPayload } from "@/lib/api-client";

const FIELDS: {
  key: "primary_color" | "secondary_color" | "accent_color";
  label: string;
  help: string;
}[] = [
  { key: "primary_color", label: "Primary", help: "Used for backgrounds, headings, dominant area." },
  { key: "secondary_color", label: "Secondary", help: "Body content surfaces." },
  { key: "accent_color", label: "Accent", help: "Highlights, links, single accent per page." },
];

const NEUTRALS: { key: keyof Neutrals; label: string }[] = [
  { key: "stone", label: "Stone" },
  { key: "hairline", label: "Hairline" },
  { key: "fog", label: "Fog" },
];

type Props = {
  value: UpdateBrandPayload;
  onChange: (next: UpdateBrandPayload) => void;
};

export function PaletteEditor({ value, onChange }: Props) {
  return (
    <div className="flex flex-col gap-6">
      <fieldset className="flex flex-col gap-3">
        <legend className="font-display text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Brand colours
        </legend>
        {FIELDS.map((f) => (
          <div key={f.key} className="grid grid-cols-[80px_1fr_140px] items-center gap-3">
            <input
              type="color"
              value={value[f.key]}
              onChange={(e) =>
                onChange({ ...value, [f.key]: e.target.value.toUpperCase() })
              }
              aria-label={f.label}
              className="h-10 w-full cursor-pointer rounded border border-brand-hairline"
            />
            <div className="flex flex-col">
              <Label className="text-sm">{f.label}</Label>
              <span className="text-xs text-muted-foreground">{f.help}</span>
            </div>
            <Input
              value={value[f.key]}
              onChange={(e) =>
                onChange({ ...value, [f.key]: e.target.value.toUpperCase() })
              }
              maxLength={7}
              className="font-mono"
            />
          </div>
        ))}
      </fieldset>

      <fieldset className="flex flex-col gap-3">
        <legend className="font-display text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Neutrals
        </legend>
        {NEUTRALS.map((f) => (
          <div key={f.key} className="grid grid-cols-[80px_1fr_140px] items-center gap-3">
            <input
              type="color"
              value={value.neutrals[f.key]}
              onChange={(e) =>
                onChange({
                  ...value,
                  neutrals: { ...value.neutrals, [f.key]: e.target.value.toUpperCase() },
                })
              }
              aria-label={f.label}
              className="h-10 w-full cursor-pointer rounded border border-brand-hairline"
            />
            <Label className="text-sm">{f.label}</Label>
            <Input
              value={value.neutrals[f.key]}
              onChange={(e) =>
                onChange({
                  ...value,
                  neutrals: { ...value.neutrals, [f.key]: e.target.value.toUpperCase() },
                })
              }
              maxLength={7}
              className="font-mono"
            />
          </div>
        ))}
      </fieldset>

      <fieldset className="flex flex-col gap-3">
        <legend className="font-display text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Typography
        </legend>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="font-heading" className="text-sm">
              Heading family
            </Label>
            <Input
              id="font-heading"
              value={value.font_heading}
              onChange={(e) => onChange({ ...value, font_heading: e.target.value })}
              maxLength={200}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="font-body" className="text-sm">
              Body family
            </Label>
            <Input
              id="font-body"
              value={value.font_body}
              onChange={(e) => onChange({ ...value, font_body: e.target.value })}
              maxLength={200}
            />
          </div>
        </div>
        <p className="text-xs text-muted-foreground">
          The deck renderer falls back to Aptos / system fonts when the named family
          isn&apos;t embedded. For exact match, supply licensed font files later.
        </p>
      </fieldset>
    </div>
  );
}
