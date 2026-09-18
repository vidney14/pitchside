import { useEffect, useState } from "react";
import "./App.css";
import { api } from "./api";
import { useEventStream } from "./useEventStream";
import EventFeed from "./components/EventFeed";
import StatsPanel from "./components/StatsPanel";
import FailuresPanel from "./components/FailuresPanel";
import EvalPanel from "./components/EvalPanel";
import RunControls from "./components/RunControls";

const TABS = ["Live Feed", "Failures & Fixes", "Eval Results"];

export default function App() {
  const { events, connected, clear } = useEventStream();
  const [scenarios, setScenarios] = useState([]);
  const [running, setRunning] = useState(false);
  const [tab, setTab] = useState(TABS[0]);
  const [statsKey, setStatsKey] = useState(0);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.scenarios().then(setScenarios).catch(() => {});
  }, []);

  useEffect(() => {
    const id = setInterval(() => {
      api.status().then((s) => setRunning(s.running)).catch(() => {});
    }, 1500);
    return () => clearInterval(id);
  }, []);

  const start = async (ids, provider, delay) => {
    setError(null);
    try {
      await api.start({ scenario_ids: ids, provider, delay });
      setRunning(true);
      setStatsKey((k) => k + 1);
    } catch (e) {
      setError(e.message);
    }
  };

  const stop = async () => {
    await api.stop().catch(() => {});
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Pitchside</h1>
        <p className="muted">self-healing football event pipeline — live dashboard</p>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <div className="app-layout">
        <aside className="app-sidebar">
          <RunControls scenarios={scenarios} running={running} onStart={start} onStop={stop} onClear={clear} />
          <StatsPanel refreshKey={statsKey} />
        </aside>

        <main className="app-main">
          <nav className="tabs">
            {TABS.map((t) => (
              <button key={t} className={`tab ${tab === t ? "active" : ""}`} onClick={() => setTab(t)}>
                {t}
              </button>
            ))}
          </nav>

          {tab === "Live Feed" && <EventFeed events={events} connected={connected} />}
          {tab === "Failures & Fixes" && <FailuresPanel events={events} scenarios={scenarios} />}
          {tab === "Eval Results" && <EvalPanel />}
        </main>
      </div>
    </div>
  );
}
