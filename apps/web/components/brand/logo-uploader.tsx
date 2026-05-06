"use client";

import Image from "next/image";
import { Upload, X } from "lucide-react";
import { useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { backendUrl } from "@/lib/api-client";
import { cn } from "@/lib/utils";

type Props = {
  existingLogoUrl: string | null;
  onFileSelected: (file: File | null) => void;
};

export function LogoUploader({ existingLogoUrl, onFileSelected }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [filename, setFilename] = useState<string | null>(null);

  const displayUrl =
    previewUrl ?? (existingLogoUrl ? backendUrl(existingLogoUrl) : null);

  const handleFile = (file: File | null) => {
    if (file) {
      setPreviewUrl(URL.createObjectURL(file));
      setFilename(file.name);
    } else {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
      setFilename(null);
    }
    onFileSelected(file);
  };

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-4">
        <div
          className={cn(
            "flex size-24 items-center justify-center rounded-md border border-brand-hairline bg-brand-fog/40",
          )}
        >
          {displayUrl ? (
            <Image
              src={displayUrl}
              alt="Brand logo"
              width={80}
              height={80}
              className="max-h-20 max-w-20 object-contain"
              unoptimized
            />
          ) : (
            <span className="text-xs text-muted-foreground">No logo</span>
          )}
        </div>

        <div className="flex flex-col gap-2">
          <input
            ref={inputRef}
            type="file"
            accept="image/png,image/jpeg,image/svg+xml,image/webp"
            className="hidden"
            onChange={(e) => handleFile(e.target.files?.[0] ?? null)}
          />
          <div className="flex items-center gap-2">
            <Button type="button" variant="outline" size="sm" onClick={() => inputRef.current?.click()}>
              <Upload className="size-4" aria-hidden /> Upload logo
            </Button>
            {previewUrl && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => handleFile(null)}
              >
                <X className="size-4" aria-hidden /> Cancel change
              </Button>
            )}
          </div>
          {filename && (
            <p className="text-xs text-muted-foreground">Pending upload: {filename}</p>
          )}
          <p className="text-xs text-muted-foreground">
            PNG, JPG, WebP, or SVG. Used in the slide deck and the workspace header.
          </p>
        </div>
      </div>
    </div>
  );
}
