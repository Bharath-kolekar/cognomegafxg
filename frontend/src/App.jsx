import React, { useEffect, useRef, useState } from 'react'

const LS_KEYS = {
  engine: 'cgx_engine',
  cloned: 'cgx_cloned',
  ttsText: 'cgx_ttsText',
  api: 'cgx_api',
  lang: 'cgx_lang',
  voice: 'cgx_voice'
}

function getInitialApi() {
  try {
    const ls = localStorage.getItem(LS_KEYS.api)
    if (ls && ls !== 'null' && ls !== 'undefined') return JSON.parse(ls)
  } catch {}
  return import.meta.env.VITE_API_URL || 'http://localhost:8000'
}
const defaultAPI = getInitialApi()

function usePersistentState(key, initial) {
  const [val, setVal] = useState(() => {
    try {
      const raw = localStorage.getItem(key)
      if (raw === null) return initial
      return JSON.parse(raw)
    } catch (_) {
      return initial
    }
  })
  useEffect(() => {
    try { localStorage.setItem(key, JSON.stringify(val)) } catch {}
  }, [key, val])
  return [val, setVal]
}

function Settings({open, onClose, api, setApi, lang, setLang, clearAll, previewVoice}){
  if (!open) return null
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white w-full max-w-lg rounded-2xl shadow-xl p-5 grid gap-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">Settings</h2>
          <button className="px-3 py-1 rounded-xl border" onClick={onClose}>Close</button>
        </div>
        <div className="grid gap-2">
          <label className="text-sm">Backend API URL</label>
          <input className="border rounded-xl p-2" value={api} onChange={(e)=>setApi(e.target.value.replace(/\/+$/,''))} placeholder="http://localhost:8000" />
          <p className="text-xs opacity-70">Used for all API calls. Stored locally.</p>
        </div>
        <div className="grid gap-2">
          <label className="text-sm">Default Language (hint)</label>
          <select className="border rounded-xl p-2" value={lang} onChange={(e)=>setLang(e.target.value)}>
            <option value="auto">Auto</option>
            <option value="en">English</option>
            <option value="hi">Hindi</option>
            <option value="ta">Tamil</option>
            <option value="te">Telugu</option>
            <option value="kn">Kannada</option>
          </select>
        </div>
        <div className="flex items-center gap-3">
          <button className="px-3 py-2 rounded-xl border" onClick={previewVoice}>Preview Voice</button>
          <button className="px-3 py-2 rounded-xl border" onClick={clearAll}>Clear saved settings</button>
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const [listening, setListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [ttsText, setTtsText] = usePersistentState(LS_KEYS.ttsText, 'Hello from MegaFX, now with XTTS v2!')
  const [audioUrl, setAudioUrl] = useState(null)
  const [engine, setEngine] = usePersistentState(LS_KEYS.engine, 'auto')
  const [cloned, setCloned] = usePersistentState(LS_KEYS.cloned, false)
  const [voice, setVoice] = usePersistentState(LS_KEYS.voice, '')
  const [lastEngine, setLastEngine] = useState('')
  const [api, setApi] = usePersistentState(LS_KEYS.api, defaultAPI)
  const [lang, setLang] = usePersistentState(LS_KEYS.lang, 'auto')
  const [showSettings, setShowSettings] = useState(false)
  const [backendOnline, setBackendOnline] = useState(false)
  const [voices, setVoices] = useState([])
  const mediaRecRef = useRef(null)
  const chunksRef = useRef([])

  const apiBase = (typeof api === 'string' && api) ? api : defaultAPI

  // Ping backend health
  useEffect(()=>{
    let cancelled = false
    async function ping(){
      try {
        const r = await fetch(`${apiBase}/health`, { cache: 'no-store' })
        if (!cancelled) setBackendOnline(r.ok)
      } catch { if (!cancelled) setBackendOnline(false) }
    }
    ping()
    const id = setInterval(ping, 4000)
    return ()=>{ cancelled = true; clearInterval(id) }
  }, [apiBase])

  // Load voices
  useEffect(()=>{
    (async ()=>{
      try {
        const r = await fetch(`${apiBase}/api/v1/voice/voices`, { cache: 'no-store' })
        if (!r.ok) return
        const data = await r.json()
        setVoices(data.voices || [])
        if (!voice && data.voices && data.voices.length) setVoice(data.voices[0].id)
      } catch {}
    })()
  }, [apiBase])

  const toggleMic = async () => {
    if (listening) {
      setListening(false)
      mediaRecRef.current && mediaRecRef.current.stop && mediaRecRef.current.stop()
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mr = new MediaRecorder(stream)
      chunksRef.current = []
      mr.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data) }
      mr.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        const form = new FormData()
        form.append('audio', blob, 'clip.webm')
        const res = await fetch(`${apiBase}/api/v1/voice/transcribe`, { method: 'POST', body: form })
        const data = await res.json()
        setTranscript(data.text || '(no text)')
      }
      mr.start()
      setListening(true)
      mediaRecRef.current = mr
    } catch (e) {
      alert('Mic recording failed: ' + e.message)
    }
  }

  const doTTS = async () => {
    const payload = { text: ttsText, engine, cloned, voice }
    const res = await fetch(`${apiBase}/api/v1/voice/speak`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    if (!res.ok) {
      const msg = await res.text()
      alert('TTS failed: ' + msg)
      return
    }
    const engineHeader = res.headers.get('X-TTS-Engine') || ''
    setLastEngine(engineHeader)
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    setAudioUrl(url)
    const audio = new Audio(url)
    audio.play()
  }

  const previewVoice = async () => {
    const res = await fetch(`${apiBase}/api/v1/voice/speak`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: 'This is a short preview of your current voice selection.', engine, cloned, voice })
    })
    if (!res.ok) return alert('Preview failed. Is backend running?')
    const engineHeader = res.headers.get('X-TTS-Engine') || ''
    setLastEngine(engineHeader)
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    setAudioUrl(url)
    const audio = new Audio(url)
    audio.play()
  }

  const clearAll = () => {
    Object.values(LS_KEYS).forEach(k => localStorage.removeItem(k))
    setEngine('auto'); setCloned(false); setTtsText('Hello from MegaFX, now with XTTS v2!');
    setVoice(''); setApi(defaultAPI); setLang('auto')
  }

  const Badge = ({label, ok}) => (
    <span className={"px-2 py-1 rounded-full border text-xs " + (ok ? "opacity-90" : "opacity-60")}>
      {label}
    </span>
  )

  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-4 p-6">
      <div className="w-full max-w-2xl flex items-center justify-between">
        <h1 className="text-3xl font-bold">Cognomegafx — Full Max v0.3.0</h1>
        <div className="flex items-center gap-2">
          <Badge label={backendOnline ? "Backend: Online" : "Backend: Offline"} ok={backendOnline} />
          <button className="px-3 py-2 rounded-xl border" onClick={()=>setShowSettings(true)}>Settings</button>
        </div>
      </div>

      <p className="opacity-80 text-center max-w-xl">
        XTTS premium voices + Piper fallback. Choose engine, voice, and preview. Settings persist.
      </p>

      <div className="flex flex-wrap items-center gap-3">
        <label className="text-sm">Engine</label>
        <select className="border rounded-lg p-2" value={engine} onChange={e=>setEngine(e.target.value)}>
          <option value="auto">Auto (prefer XTTS)</option>
          <option value="xtts">XTTS (premium)</option>
          <option value="piper">Piper (fast)</option>
        </select>

        <label className="text-sm">Voice</label>
        <select className="border rounded-lg p-2" value={voice} onChange={e=>setVoice(e.target.value)}>
          {voices.map(v => <option key={v.id} value={v.id}>{v.label}</option>)}
        </select>

        <label className="text-sm flex items-center gap-2">
          <input type="checkbox" checked={cloned} onChange={e=>setCloned(e.target.checked)} />
          Use cloned voice
        </label>

        {lastEngine && <Badge label={`Last: ${lastEngine}`} ok />}
      </div>

      <div className="grid gap-2 w-full max-w-2xl">
        <button onClick={toggleMic} className="px-4 py-2 rounded-xl border">{listening ? 'Stop & Transcribe' : 'Record & Transcribe'}</button>
        <textarea className="w-full h-28 p-3 rounded-xl border" placeholder="Transcript will appear here..." value={transcript} onChange={e=>setTranscript(e.target.value)} />
      </div>

      <div className="grid gap-2 w-full max-w-2xl">
        <input className="w-full p-3 rounded-xl border" value={ttsText} onChange={e=>setTtsText(e.target.value)} />
        <button onClick={doTTS} className="px-4 py-2 rounded-xl border">Speak (TTS)</button>
        {audioUrl && <audio controls src={audioUrl}/>}
      </div>

      <Settings
        open={showSettings}
        onClose={()=>setShowSettings(false)}
        api={api}
        setApi={setApi}
        lang={lang}
        setLang={setLang}
        clearAll={clearAll}
        previewVoice={previewVoice}
      />
    </div>
  )
}
