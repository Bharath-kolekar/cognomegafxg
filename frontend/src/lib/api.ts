/* eslint-disable @typescript-eslint/no-explicit-any */

// ---- Config ---------------------------------------------------------------

const BASE =
  (import.meta as any)?.env?.VITE_API_BASE?.replace(/\/+$/, "") ||
  "http://127.0.0.1:8000";

// ---- Types ----------------------------------------------------------------

export type VoiceItem = {
  id: string;          // "xtts_default" | "xtts_cloned" | "piper_default" | ...
  label: string;       // human label
  engine: string;      // "xtts" | "piper" | ...
};

export type VoicesResponse = {
  voices: VoiceItem[];
};

export type SpeakOnceParams = {
  text: string;
  voice: string;       // e.g. "xtts_default" | "xtts_cloned"
  language?: string;   // e.g. "en", "hi" (omit if auto)
  signal?: AbortSignal;
};

export type SpeakLongParams = {
  text: string;
  voice: string;
  language?: string;         // fixed language (omit if using auto)
  auto_language?: boolean;   // default true
  max_chars?: number;        // default 500
  signal?: AbortSignal;
};

// ---- Helpers --------------------------------------------------------------

function normalizeError(status: number, txt: string, statusText: string) {
  let msg = (txt || "").trim();
  try {
    const j = JSON.parse(msg);
    if (j?.detail) msg = j.detail;
  } catch {
    /* not json */
  }
  if (!msg) msg = `HTTP ${status} ${statusText || ""}`.trim();
  return msg;
}

async function fetchJson<T>(
  url: string,
  init?: RequestInit
): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(normalizeError(res.status, body, res.statusText));
  }
  return (await res.json()) as T;
}

async function fetchBlob(
  url: string,
  init?: RequestInit
): Promise<Blob> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(normalizeError(res.status, body, res.statusText));
  }
  return await res.blob();
}

// Convenience: turn a Blob into an object URL (remember to revoke later)
export function blobToUrl(b: Blob): string {
  return URL.createObjectURL(b);
}

// ---- Health / Debug -------------------------------------------------------

export async function getHealth(signal?: AbortSignal) {
  return await fetchJson<{ ok: boolean; version: string }>(
    `${BASE}/health`,
    { method: "GET", signal }
  );
}

// ---- Voices ---------------------------------------------------------------

export async function getVoices(signal?: AbortSignal): Promise<VoicesResponse> {
  return await fetchJson<VoicesResponse>(`${BASE}/api/v1/voice/voices`, {
    method: "GET",
    signal,
  });
}

// alias (if some components call a different name)
export const fetchNeuralVoices = getVoices;

// ---- TTS: single-shot -----------------------------------------------------

export async function speakOnce(params: SpeakOnceParams): Promise<Blob> {
  const { text, voice, language, signal } = params;
  return await fetchBlob(`${BASE}/api/v1/voice/speak`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, voice, language }),
    signal,
  });
}

// ---- TTS: long text (chunk + concat on server) ---------------------------

export async function speakLong(params: SpeakLongParams): Promise<Blob> {
  const {
    text,
    voice,
    language,
    auto_language = true,
    max_chars = 500,
    signal,
  } = params;
  return await fetchBlob(`${BASE}/api/v1/voice/speak_long`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, voice, language, auto_language, max_chars }),
    signal,
  });
}

// ---- Optional: HTML cleaning endpoints (only if your backend exposes them)

export async function cleanHtml(html: string, signal?: AbortSignal): Promise<{
  title: string;
  text: string;
}> {
  try {
    return await fetchJson<{ title: string; text: string }>(
      `${BASE}/api/v1/content/clean`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ html }),
        signal,
      }
    );
  } catch (err: any) {
    // If you don't have content router enabled, gracefully degrade
    if (String(err?.message || err).includes("404")) {
      return { title: "", text: html };
    }
    throw err;
  }
}

export async function cleanHtmlFile(file: File, signal?: AbortSignal): Promise<{
  title: string;
  text: string;
}> {
  const form = new FormData();
  form.append("file", file);
  try {
    return await fetchJson<{ title: string; text: string }>(
      `${BASE}/api/v1/content/clean_file`,
      { method: "POST", body: form, signal }
    );
  } catch (err: any) {
    if (String(err?.message || err).includes("404")) {
      // Fallback: read file text client-side (basic)
      const txt = await file.text();
      return { title: file.name, text: txt };
    }
    throw err;
  }
}

// ---- Optional: STT (if you keep this route) -------------------------------

export async function transcribe(file: File, signal?: AbortSignal): Promise<{
  text: string;
  request_id?: string;
}> {
  const form = new FormData();
  form.append("audio", file);
  return await fetchJson<{ text: string; request_id?: string }>(
    `${BASE}/api/v1/voice/transcribe`,
    { method: "POST", body: form, signal }
  );
}
