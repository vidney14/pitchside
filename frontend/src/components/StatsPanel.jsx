import { useEffect, useState } from "react";
import { api } from "../api";

export default function StatsPanel({ refreshKey }) {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    let alive = true;
    const load = () => api.stats().then((s) => alive && setStats(s)).catch(() => {});
    load();
    const id = setInterval(load, 2000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [refreshKey]);

  if (!stats) return <div className="panel"><h2>Match Stats</h2><p className="muted">loading…</p></div>;

  const teams = Object.entries(stats.by_team || {});
  const types = Object.entries(stats.by_event_type || {}).slice(0, 8);
  const stages = stats.audit_by_stage || {};

  return (
    <div className="panel">
      <h2>Match Stats</h2>
      <div className="stat-total">{stats.total_events} <span className="muted">events ingested</span></div>

      <div className="stat-block">
        <h3>By team</h3>
        {teams.length === 0 && <p className="muted">—</p>}
        {teams.map(([team, count]) => (
          <div className="bar-row" key={team}>
            <span className="bar-label">{team}</span>
            <div className="bar-track">
              <div className="bar-fill" style={{ width: `${(count / stats.total_events) * 100}%` }} />
            </div>
            <span className="bar-value">{count}</span>
          </div>
        ))}
      </div>

      <div className="stat-block">
        <h3>Top event types</h3>
        {types.map(([type, count]) => (
          <div className="bar-row" key={type}>
            <span className="bar-label">{type}</span>
            <div className="bar-track">
              <div className="bar-fill bar-fill-alt" style={{ width: `${(count / types[0][1]) * 100}%` }} />
            </div>
            <span className="bar-value">{count}</span>
          </div>
        ))}
      </div>

      <div className="stat-block">
        <h3>Audit by stage</h3>
        <div className="chip-row">
          {Object.entries(stages).map(([stage, count]) => (
            <span className="chip" key={stage}>{stage}: {count}</span>
          ))}
        </div>
      </div>
    </div>
  );
}
