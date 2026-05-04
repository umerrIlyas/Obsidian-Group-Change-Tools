"use client";

import { Upload } from "lucide-react";
import { useCallback, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { ApiError, api } from "@/lib/api-client";
import { cn } from "@/lib/utils";

const ACCEPTED = ".docx,.xlsx,.pdf,.png,.jpg,.jpeg,.svg";

type Props = {
  projectId: string;
  onUploaded?: () => void;
};

export function DocumentDropzone({ projectId, onUploaded }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  const upload = useCallback(
    async (files: FileList | File[]) => {
      setError(null);
      const list = Array.from(files);
      if (!list.length) return;
      setUploading((prev) => [...prev, ...list.map((f) => f.name)]);
      try {
        await Promise.all(list.map((file) => api.documents.upload(projectId, file)));
        onUploaded?.();
      } catch (e) {
        setError(e instanceof ApiError ? e.message : (e as Error).message);
      } finally {
        setUploading((prev) =>
          prev.filter((name) => !list.some((f) => f.name === name)),
        );
      }
    },
    [projectId, onUploaded],
  );

  return (
    <div
      role="button"
      tabIndex={0}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsDragging(false);
        if (e.dataTransfer.files.length) void upload(e.dataTransfer.files);
      }}
      onClick={() => inputRef.current?.click()}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
      }}
      className={cn(
        "flex cursor-pointer flex-col items-center gap-3 rounded-lg border-2 border-dashed border-brand-hairline bg-background p-8 text-center transition-colors hover:border-brand-accent hover:bg-brand-fog/40",
        isDragging && "border-brand-accent bg-brand-fog/60",
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED}
        className="hidden"
        multiple
        onChange={(e) => {
          if (e.target.files?.length) void upload(e.target.files);
          e.target.value = "";
        }}
      />
      <Upload className="size-6 text-brand-accent" aria-hidden />
      <div>
        <p className="text-sm font-medium">Drop files to upload</p>
        <p className="mt-1 text-xs text-muted-foreground">
          Supported: .docx, .xlsx, .pdf, .png, .jpg
        </p>
      </div>
      <Button type="button" variant="outline" size="sm">
        Choose files
      </Button>
      {uploading.length > 0 && (
        <p className="text-xs text-muted-foreground">
          Uploading: {uploading.join(", ")}
        </p>
      )}
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}
