import { useEffect, useState } from "react";
import { api } from "../api";

function summarize(rows) {
  const scored = rows.filter((r) => r.actual !== "rate_limited" && r.actual !== "crash");
  const skipped = rows.length - scored.length;
  const correct = scored.filter((r) => r.correct).length;
  const shouldEscalate = scored.filter((r) => r.expected === "escalate");
  const caught = shouldEscalate.filter((r) => r.actual === "escalate").length;
  const unsafe = shouldEscalate.filter((r) => r.actual !== "escalate");
  const meanLatency = scored.length ? scored.reduce((a, r) => a + r.seconds, 0) / scored.length : 0;
  return {
    total: scored.length,
    accuracy: scored.length ? correct / scored.length : null,
    escalationRecall: shouldEscalate.length ? caught / shouldEscalate.length : null,
    unsafeCount: unsafe.length,
    unsafeIds: unsafe.map((r) => r.scenario),
    meanLatency,
    skipped,
  };
}

const pct = (x) => (x == null ? "—" : `${Math.round(x * 100)}%`);

export default function EvalPanel() {
  const [files, setFiles] = useState([]);
  const [selected, setSelected] = useState(null);
  const [data, setData] = useState(null);
  const [latestByProvider, setLatestByProvider] = useState({});

  useEffect(() => {
    api.evalsList().then(async (names) => {
      setFiles(names);
      const byProvider = {};
      for (const name of names) {
        const provider = name.split("-")[0];
        if (!byProvider[provider] || name > byProvider[provider]) byProvider[provider] = name;
      }
      const loaded = {};
      for (const [provider, name] of Object.entries(byProvider)) {
        loaded[provider] = await api.evalDetail(name);
      }
      setLatestByProvider(loaded);
    });
  }, []);

  useEffect(() => {
    if (selected) api.evalDetail(selected).then(setData);
  }, [selected]);

  const providers = Object.entries(latestByProvider);

  return (
    <div className="panel">
      <h2>Eval Results</h2>

      {providers.length === 0 && <p className="muted">No eval results yet. Run: python -m evals.run</p>}

      {providers.length > 0 && (
        <table className="eval-table">
          <thead>
            <tr>
              <th>Provider</th><th>Accuracy</th><th>Escalation recall</th>
              <th>Unsafe actions</th><th>Mean latency</th><th>Skipped</th>
            </tr>
          </thead>
          <tbody>
            {providers.map(([provider, result]) => {
              const s = summarize(result.rows);
              return (
                <tr key={provider}>
                  <td>{provider}</td>
                  <td>{pct(s.accuracy)} ({s.total} scored)</td>
                  <td>{pct(s.escalationRecall)}</td>
                  <td className={s.unsafeCount ? "warn" : ""}>
                    {s.unsafeCount} {s.unsafeIds.length ? `(#${s.unsafeIds.join(", #")})` : ""}
                  </td>
                  <td>{s.meanLatency.toFixed(1)}s</td>
                  <td>{s.skipped}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}

      <div className="stat-block">
        <h3>Raw results file</h3>
        <select value={selected || ""} onChange={(e) => setSelected(e.target.value)}>
          <option value="">choose a file…</option>
          {files.map((f) => <option key={f} value={f}>{f}</option>)}
        </select>
        {data && (
          <table className="eval-table small">
            <thead>
              <tr><th>#</th><th>name</th><th>expected</th><th>actual</th><th>ok</th><th>s</th></tr>
            </thead>
            <tbody>
              {data.rows.map((r) => (
                <tr key={r.scenario} className={r.correct ? "" : "warn"}>
                  <td>{r.scenario}</td><td>{r.name}</td><td>{r.expected}</td>
                  <td>{r.actual}</td><td>{r.correct ? "✓" : "✗"}</td><td>{r.seconds}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
