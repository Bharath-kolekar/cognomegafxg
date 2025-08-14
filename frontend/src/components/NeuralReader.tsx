import React, { useRef, useState } from "react";
import { speakLong, cleanHtml, cleanHtmlFile } from "../lib/api";

/**
 * NeuralReader
 * - Paste/Upload HTML -> clean -> preview
 * - Speak long text via server-side chunking + concat
 * - Controls:
 *   - Auto-detect language (checkbox)
 *   - Max chars per chunk (default 500; 200–2000)
 */
export default function NeuralReader() {
  // raw -> clean
  const [rawHtml, setRawHtml] = useState("");
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");

  // language & chunking controls
  const [language, setLanguage] = useState("en");
  const [autoLang, setAutoLang] = useState(true);     // NEW
  const [maxChars, setMaxChars] = useState(500);       // NEW

  // ui state
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  async function onPasteClean() {
    setErr(null);
    if (!rawHtml.trim()) { setErr("Paste some HTML first."); return; }
    setBusy(true);
    try {
      const out = await cleanHtml(rawHtml);
      setTitle(out.title || "");
      setText(out.text || "");
    } catch (e: any) {
      setErr(e.message || String(e));
    } finally {
      setBusy(false);
    }
  }

  async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    setErr(null);
    const f = e.target.files?.[0];
    if (!f) return;
    setBusy(true);
    try {
      const out = await cleanHtmlFile(f);
      setTitle(out.title || "");
      setText(out.text || "");
    } catch (e: any) {
      setErr(e.message || String(e));
    } finally {
      setBusy(false);
    }
  }

  async function onSpeak() {
    setErr(null);
    if (!text.trim()) { setErr("No cleaned text to speak."); return; }
    setBusy(true);
    try {
      // when autoLang is true, we omit language so backend can auto-detect
      const langArg = autoLang ? undefined : language;
      const blob = await speakLong({
        text,
        voice: "xtts_cloned",   // or make this a dropdown if you want
        language: langArg,
        auto_language: autoLang,
        max_chars: maxChars,
      });
      const url = URL.createObjectURL(blob);
      if (audioRef.current) {
        audioRef.current.src = url;
        audioRef.current.play().catch(() => {});
      }
    } catch (e: any) {
      setErr(e.message || String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="w-full max-w-4xl mx-auto mt-8 rounded-2xl p-4 md:p-6 shadow-lg bg-neutral-900/60 border border-neutral-800 backdrop-blur">
      <h2 className="text-xl md:text-2xl font-semibold mb-4 text-white">Neural Reader</h2>

      {/* top row: file, language, auto-detect, chunk size, speak */}
      <div className="flex flex-col md:flex-row gap-3 mb-3">
        <input
          type="file"
          accept=".html,.htm,.xhtml,.mhtml,.txt"
          onChange={onFile}
          className="text-neutral-200"
        />

        {/* language (hint) */}
        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          disabled={autoLang}
          title={autoLang ? "Disabled when Auto-detect is on" : "Preferred language"}
          className={`rounded-lg p-2 border border-neutral-700 ${
            autoLang ? "bg-neutral-800/50 text-neutral-400" : "bg-neutral-800 text-white"
          }`}
        >
          <option value="en">English (en)</option>
          <option value="hi">Hindi (hi)</option>
          <option value="ta">Tamil (ta)</option>
          <option value="te">Telugu (te)</option>
          <option value="es">Spanish (es)</option>
          <option value="de">German (de)</option>
        </select>

        {/* NEW: auto-detect toggle */}
        <label className="inline-flex items-center gap-2 text-neutral-300">
          <input
            type="checkbox"
            className="h-4 w-4"
            checked={autoLang}
            onChange={(e) => setAutoLang(e.target.checked)}
          />
          Auto-detect language
        </label>

        {/* NEW: max chars per chunk */}
        <div className="flex items-center gap-2">
          <label className="text-neutral-300 text-sm">Max chars</label>
          <input
            type="number"
            min={200}
            max={2000}
            step={50}
            value={maxChars}
            onChange={(e) =>
              setMaxChars(Math.max(200, Math.min(2000, Number(e.target.value) || 500)))
            }
            className="w-24 rounded-lg bg-neutral-800 text-white p-2 border border-neutral-700"
          />
        </div>

        <button
          onClick={onSpeak}
          disabled={busy}
          className="rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-medium py-2 px-4"
        >
          {busy ? "Speaking…" : "Speak Clean Text"}
        </button>
      </div>

      {/* left: paste html & clean; right: cleaned output */}
      <div className="grid md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm text-neutral-300 mb-1">Paste HTML</label>
          <textarea
            value={rawHtml}
            onChange={(e) => setRawHtml(e.target.value)}
            rows={12}
            className="w-full rounded-xl bg-neutral-800 text-white p-3 border border-neutral-700"
            placeholder="Paste raw HTML here…"
          />
          <button
            onClick={onPasteClean}
            disabled={busy}
            className="mt-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium py-2 px-4"
          >
            {busy ? "Cleaning…" : "Clean"}
          </button>
        </div>

        <div>
          <label className="block text-sm text-neutral-300 mb-1">Clean Title</label>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full rounded-xl bg-neutral-800 text-white p-2 border border-neutral-700 mb-2"
            placeholder="(optional)"
          />
          <label className="block text-sm text-neutral-300 mb-1">Clean Text</label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={12}
            className="w-full rounded-xl bg-neutral-800 text-white p-3 border border-neutral-700"
            placeholder="(cleaned content appears here)"
          />
        </div>
      </div>

      {err && <div className="mt-3 text-rose-400 text-sm">{err}</div>}
      <audio ref={audioRef} controls className="mt-4 w-full" />
    </div>
  );
}
