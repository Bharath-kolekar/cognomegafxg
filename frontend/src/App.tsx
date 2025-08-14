import React from "react";
import NeuralVoicePanel from "./components/NeuralVoicePanel";
import NeuralReader from "./components/NeuralReader";

export default function App() {
  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 p-4 md:p-8 space-y-8">
      <NeuralVoicePanel />
      <NeuralReader />
    </div>
  );
}
