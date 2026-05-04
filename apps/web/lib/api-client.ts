/**
 * Typed fetch wrapper for the FastAPI backend.
 *
 * - Reads the base URL from NEXT_PUBLIC_API_URL (default: http://localhost:8000)
 * - Surfaces backend errors in a single shape so call sites can handle them uniformly.
 */

export type ApiErrorBody = {
  error: { code: string; message: string };
};

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type RequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
  searchParams?: Record<string, string | number | boolean | undefined>;
};

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const url = new URL(path.replace(/^\/+/, ""), `${BASE_URL.replace(/\/+$/, "")}/`);
  if (options.searchParams) {
    for (const [key, value] of Object.entries(options.searchParams)) {
      if (value !== undefined) url.searchParams.set(key, String(value));
    }
  }

  const isJsonBody =
    options.body !== undefined &&
    !(options.body instanceof FormData) &&
    !(options.body instanceof Blob);

  const response = await fetch(url, {
    ...options,
    headers: {
      Accept: "application/json",
      ...(isJsonBody ? { "Content-Type": "application/json" } : {}),
      ...(options.headers ?? {}),
    },
    body: isJsonBody ? JSON.stringify(options.body) : (options.body as BodyInit | undefined),
  });

  if (!response.ok) {
    let body: ApiErrorBody | null = null;
    try {
      body = (await response.json()) as ApiErrorBody;
    } catch {
      // ignore, fall back to status text
    }
    throw new ApiError(
      response.status,
      body?.error?.code ?? "http_error",
      body?.error?.message ?? response.statusText,
    );
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export type Project = {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
};

export type DocumentStatus =
  | "uploaded"
  | "parsing"
  | "chunking"
  | "embedding"
  | "ready"
  | "failed";

export type DocumentSummary = {
  id: string;
  project_id: string;
  kind: string;
  filename: string;
  content_type: string | null;
  size_bytes: number;
  status: DocumentStatus;
  error: string | null;
  ingested_at: string | null;
  created_at: string;
};

export type DocumentDetail = DocumentSummary & {
  raw_text_excerpt: string | null;
  meta: Record<string, unknown>;
};

export type RetrievedHit = {
  chunk_id: string;
  document_id: string;
  document_filename: string;
  document_kind: string;
  score: number;
  text: string;
  meta: Record<string, unknown>;
};

export type RetrieveResponse = {
  query: string;
  hits: RetrievedHit[];
};

export const api = {
  health: () =>
    apiFetch<{
      status: string;
      version: string;
      app_env: string;
      llm_provider: string;
      llm_credentials: boolean;
      embedding_provider: string;
      embedding_dim: number;
      tracing_enabled: boolean;
    }>("/health"),

  projects: {
    list: () => apiFetch<Project[]>("/projects"),
    get: (id: string) => apiFetch<Project>(`/projects/${id}`),
    create: (body: { name: string; description?: string | null }) =>
      apiFetch<Project>("/projects", { method: "POST", body }),
  },

  documents: {
    listByProject: (projectId: string) =>
      apiFetch<DocumentSummary[]>(`/projects/${projectId}/documents`),
    get: (id: string) => apiFetch<DocumentDetail>(`/documents/${id}`),
    upload: (projectId: string, file: File) => {
      const form = new FormData();
      form.append("file", file);
      return apiFetch<DocumentSummary>(`/projects/${projectId}/documents`, {
        method: "POST",
        body: form,
      });
    },
  },

  retrieval: {
    query: (projectId: string, body: { query: string; top_k?: number }) =>
      apiFetch<RetrieveResponse>(`/projects/${projectId}/retrieve`, {
        method: "POST",
        body,
      }),
  },
};
