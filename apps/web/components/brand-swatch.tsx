import { cn } from "@/lib/utils";

type Swatch = {
  name: string;
  hex: string;
  role?: string;
};

const SWATCHES: Swatch[] = [
  { name: "Obsidian", hex: "#0D171E", role: "Primary" },
  { name: "Slate", hex: "#2C343C", role: "Secondary" },
  { name: "Teal", hex: "#3A8C91", role: "Accent" },
  { name: "Stone", hex: "#6B7280" },
  { name: "Hairline", hex: "#D9DEE3" },
  { name: "Fog", hex: "#EEF1F3" },
];

export function BrandSwatchGrid() {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-6">
      {SWATCHES.map((s) => (
        <div
          key={s.hex}
          className="flex flex-col gap-2 rounded-md border border-brand-hairline p-3"
        >
          <div
            className="h-12 w-full rounded"
            style={{ backgroundColor: s.hex }}
            aria-hidden
          />
          <div className="flex flex-col">
            <span className={cn("text-sm font-medium")}>{s.name}</span>
            <span className="font-mono text-[11px] text-muted-foreground">
              {s.hex}
            </span>
            {s.role && (
              <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
                {s.role}
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
