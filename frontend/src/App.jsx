import { useEffect, useMemo, useState } from "react";
import "./App.css";
import { api } from "./api";
import { useApiPoll } from "./useApiPoll";
import { useEventStream } from "./useEventStream";
import Header from "./components/Header";
import StatTiles from "./components/StatTiles";
import StageFunnelChart from "./components/StageFunnelChart";
import LiveSeriesChart from "./components/LiveSeriesChart";
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
  const [error, setError] = useState(null);

  const stats = useApiPoll(api.stats, 2000);
  const audit = useApiPoll(() => api.audit(1000), 2000);
  const rules = useApiPoll(api.rules, 3000);

  useEffect(() => {
    api.scenarios().then(setScenarios).catch(() => {});
  }, []);

  useEffect(() => {
    const id = setInterval(() => {
      api.status().then((s) => setRunning(s.running)).catch(() => {});
    }, 1500);
    return () => clearInterval(id);
  }, []);

  const headline = useMemo(() => {
    const healed = (audit || []).filter(
      (a) => a.stage === "HEALED" || (a.stage === "OK" && a.detail?.text?.includes("via rule"))
    ).length;
    const escalated = (audit || []).filter(
      (a) => a.stage === "ESCALATE" && a.detail?.text?.includes("quarantined")
    ).length;
    return {
      eventsIngested: stats?.total_events ?? 0,
      healed,
      escalated,
      rulesLearned: rules?.length ?? 0,
    };
  }, [audit, stats, rules]);

  const start = async (ids, provider, delay) => {
    setError(null);
    try {
      await api.start({ scenario_ids: ids, provider, delay });
      setRunning(true);
    } catch (e) {
      setError(e.message);
    }
  };

  const stop = async () => {
    await api.stop().catch(() => {});
  };

  return (
    <div className="app">
      {error && <div className="error-banner">{error}</div>}

      <Header running={running} />
      <StatTiles {...headline} />

      <aside className="app-sidebar">
        <RunControls scenarios={scenarios} running={running} onStart={start} onStop={stop} onClear={clear} />
        <StatsPanel stats={stats} />
      </aside>

      <div className="app-main-col">
        <StageFunnelChart byStage={stats?.audit_by_stage} />

        <div className="tab-panel-wrap">
          <nav className="tabs">
            {TABS.map((t) => (
              <button key={t} className={`tab ${tab === t ? "active" : ""}`} onClick={() => setTab(t)}>
                {t}
              </button>
            ))}
          </nav>

          <div className="tab-content">
            {tab === "Live Feed" && (
              <>
                <LiveSeriesChart events={events} />
                <EventFeed events={events} connected={connected} />
              </>
            )}
            {tab === "Failures & Fixes" && <FailuresPanel events={events} scenarios={scenarios} />}
            {tab === "Eval Results" && <EvalPanel />}
          </div>
        </div>
      </div>
    </div>
  );
}
