import React, { useEffect, useMemo, useRef, useState } from "react";
import { getVoices, speak, Voice } from "../lib/api";

export default function NeuralVoicePanel() {
  const [voices, setVoices] = useState<Voice[]>([]);
  const [language, setLanguage] = useState("en");
  const [useCloned, setUseCloned] = useState(true);
  const [text, setText] = useState("Hello! This is your Neural voice.");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setVoices(await getVoices());
      } catch (e:any) {
        setErr(e.message || String(e));
      }
    })();
  }, []);

  const selectedVoiceId = useMemo(() => {
    // prefer cloned if available
    if (useCloned) {
      const v = voices.find(v => v.id === "xtts_cloned");
      if (v) return v.id;
    }
    return voices.find(v => v.id === "xtts_default")?.id || voices[0]?.id;
  }, [voices, useCloned]);

  async function onSpeak() {
    setErr(null);
    if (!text.trim()) { setErr("Enter some text"); return; }
    if (!selectedVoiceId) { setErr("No voice available"); return; }
    setBusy(true);
    try {
      const blob = await speak(text, selectedVoiceId, language);
      const url = URL.createObjectURL(blob);
      if (audioRef.current) {
        audioRef.current.src = url;
        audioRef.current.play().catch(()=>{});
      }
    } catch (e:any) {
      setErr(e.message || String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="w-full max-w-3xl mx-auto rounded-2xl p-4 md:p-6 shadow-lg bg-neutral-900/60 border border-neutral-800 backdrop-blur">
      <h2 className="text-xl md:text-2xl font-semibold mb-4 text-white">Neural Voice</h2>

      <div className="grid md:grid-cols-3 gap-3 mb-4">
        <label className="flex flex-col text-sm text-neutral-300">
          Language
          <select
            className="mt-1 rounded-lg bg-neutral-800 text-white p-2 border border-neutral-700"
            value={language}
            onChange={(e)=>setLanguage(e.target.value)}
          >
            <option value="en">English (en)</option>
            <option value="hi">Hindi (hi)</option>
            <option value="ta">Tamil (ta)</option>
            <option value="te">Telugu (te)</option>
            <option value="es">Spanish (es)</option>
            <option value="de">German (de)</option>
            {/* add more as you like */}
          </select>
        </label>

        <div className="flex items-end">
          <label className="inline-flex items-center gap-2 text-neutral-300">
            <input
              type="checkbox"
              className="h-4 w-4"
              checked={useCloned}
              onChange={(e)=>setUseCloned(e.target.checked)}
            />
            Use cloned voice
          </label>
        </div>

        <div className="flex items-end">
          <button
            onClick={onSpeak}
            disabled={busy}
            className="w-full rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium py-2"
          >
            {busy ? "Synthesizing…" : "Preview"}
          </button>
        </div>
      </div>

      <textarea
        value={text}
        onChange={(e)=>setText(e.target.value)}
        rows={4}
        className="w-full rounded-xl bg-neutral-800 text-white p-3 border border-neutral-700"
        placeholder="Type something to speak…"
      />

      {err && <div className="mt-3 text-rose-400 text-sm">{err}</div>}

      <audio ref={audioRef} controls className="mt-4 w-full" />
    </div>
  );
}
