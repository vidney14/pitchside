import { useMemo, useState } from "react";
import { buildEpisodes, deriveTracker } from "../episodes";
import { stageColor } from "../stageStyle";

function StepTracker({ ep }) {
  const steps = deriveTracker(ep);
  return (
    <div className="step-tracker">
      {steps.map((step, i) => {
        let dotClass = step.done ? "done" : "pending";
        if (step.resolved === "healed") dotClass = "resolved-healed";
        if (step.resolved === "escalated") dotClass = "resolved-escalated";
        return (
          <div className="step" key={step.key} title={step.text || step.label}>
            <div className="step-dot-row">
              <span className={`step-dot ${dotClass}`} />
              {i < steps.length - 1 && <span className={`step-line ${step.done ? "done" : ""}`} />}
            </div>
            <span className="step-label">{step.label}</span>
          </div>
        );
      })}
    </div>
  );
}

function Episode({ ep, name }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="episode">
      <div className="episode-header">
        <span className={`resolution-badge ${ep.resolution || "open"}`}>
          {ep.resolution === "healed" ? "HEALED" : ep.resolution === "escalated" ? "ESCALATED" : "IN PROGRESS"}
        </span>
        <span className="episode-title">
          {ep.scenario ? `Scenario ${ep.scenario} — ${name || "unknown"}` : "Failure"}
        </span>
        <span className="muted episode-time">{ep.opened}</span>
      </div>

      <StepTracker ep={ep} />

      <button className="link-btn expand-btn" onClick={() => setOpen((o) => !o)}>
        {open ? "hide details" : "show details"}
      </button>
      {open && (
        <div className="episode-detail">
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
      )}
    </div>
  );
}

export default function FailuresPanel({ events, scenarios }) {
  const episodes = useMemo(() => buildEpisodes(events), [events]);
  const nameOf = (sid) => scenarios.find((s) => s.id === sid)?.name;

  return (
    <div className="panel">
      <h2>Failures &amp; Fixes</h2>
      {episodes.length === 0 && (
        <div className="empty-state">No poison pills have fired yet this run.</div>
      )}
      {episodes.map((ep, i) => (
        <Episode ep={ep} name={nameOf(ep.scenario)} key={i} />
      ))}
    </div>
  );
}
