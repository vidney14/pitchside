import { useState } from "react";

export default function RunControls({ scenarios, running, onStart, onStop, onClear }) {
  const [selected, setSelected] = useState([]);
  const [provider, setProvider] = useState("groq");
  const [delay, setDelay] = useState(0.15);
  const [busy, setBusy] = useState(false);

  const toggle = (id) =>
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));

  const selectAll = () => setSelected(scenarios.map((s) => s.id));
  const selectNone = () => setSelected([]);

  const start = async () => {
    setBusy(true);
    try {
      await onStart(selected, provider, Number(delay));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Run Controls</h2>
        <span className={`live-pill small ${running ? "is-live" : "is-idle"}`}>
          <span className="live-dot" />
          {running ? "running" : "idle"}
        </span>
      </div>

      <div className="control-row">
        <label>
          Provider
          <select value={provider} onChange={(e) => setProvider(e.target.value)} disabled={running}>
            <option value="groq">Groq</option>
            <option value="gemini">Gemini</option>
          </select>
        </label>
        <label>
          Replay delay (s)
          <input
            type="number" min="0" max="2" step="0.05"
            value={delay} onChange={(e) => setDelay(e.target.value)} disabled={running}
          />
        </label>
      </div>

      <div className="scenario-picker">
        <div className="scenario-picker-header">
          <span className="muted">Poison pills to arm ({selected.length} selected)</span>
          <span>
            <button className="link-btn" onClick={selectAll} disabled={running}>all</button>
            <button className="link-btn" onClick={selectNone} disabled={running}>none</button>
          </span>
        </div>
        <div className="scenario-grid">
          {scenarios.map((s) => (
            <label className="scenario-item" key={s.id}>
              <input
                type="checkbox"
                checked={selected.includes(s.id)}
                onChange={() => toggle(s.id)}
                disabled={running}
              />
              <span className="scenario-id">#{s.id}</span> {s.name}
            </label>
          ))}
        </div>
      </div>

      <div className="control-row">
        <button className="primary-btn" onClick={start} disabled={running || busy}>
          {busy ? "starting…" : "Start run"}
        </button>
        <button className="danger-btn" onClick={onStop} disabled={!running}>Stop</button>
        <button className="link-btn" onClick={onClear}>clear feed</button>
      </div>
    </div>
  );
}
