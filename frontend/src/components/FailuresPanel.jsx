import { useMemo } from "react";
import { buildEpisodes } from "../episodes";
import { stageColor } from "../stageStyle";

export default function FailuresPanel({ events, scenarios }) {
  const episodes = useMemo(() => buildEpisodes(events), [events]);
  const nameOf = (sid) => scenarios.find((s) => s.id === sid)?.name;

  return (
    <div className="panel">
      <h2>Failures &amp; Fixes</h2>
      {episodes.length === 0 && <p className="muted">No poison pills have fired yet this run.</p>}
      {episodes.map((ep, i) => (
        <div className="episode" key={i}>
          <div className="episode-header">
            <span className={`resolution-badge ${ep.resolution || "open"}`}>
              {ep.resolution === "healed" ? "HEALED" : ep.resolution === "escalated" ? "ESCALATED" : "IN PROGRESS"}
            </span>
            <span className="episode-title">
              {ep.scenario ? `Scenario ${ep.scenario} — ${nameOf(ep.scenario) || "unknown"}` : "Failure"}
            </span>
            <span className="muted episode-time">{ep.opened}</span>
          </div>
          <div className="episode-critical">{ep.critical}</div>
          <div className="episode-steps">
            {ep.steps.map((s, j) => (
              <div className="episode-step" key={j}>
                <span className="stage-badge small" style={{ background: stageColor(s.stage) }}>{s.stage}</span>
                <span>{s.text}</span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
