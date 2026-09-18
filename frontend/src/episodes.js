// Group the flat bus event stream into "failure episodes": one CRITICAL
// (a poison pill firing) through to its resolution (HEALED retry or
// ESCALATE). The pipeline handles one failure at a time, so a simple
// running state machine over stream order is enough -- no ids needed.
export function buildEpisodes(events) {
  const episodes = [];
  let current = null;

  for (const ev of events) {
    if (ev.stage === "CRITICAL") {
      if (current) episodes.push(current);
      current = {
        scenario: ev.detail?.scenario ?? null,
        opened: ev.at,
        critical: ev.text,
        steps: [],
        resolution: null,
      };
      continue;
    }
    if (!current) continue;

    current.steps.push(ev);

    // heal() emits an ESCALATE for the guardrail's own verdict, then
    // ingest.py emits a second, final ESCALATE ("quarantined") -- close
    // the episode on that one so both land in its step list.
    if (ev.stage === "ESCALATE" && ev.text.includes("quarantined")) {
      current.resolution = "escalated";
      episodes.push(current);
      current = null;
    } else if (ev.stage === "OK" && (ev.text.startsWith("retried") || ev.text.includes("skipped via rule"))) {
      current.resolution = "healed";
      episodes.push(current);
      current = null;
    }
  }
  if (current) episodes.push(current);
  return episodes.reverse();
}

const LLM_TRACKER = [
  { key: "detected", label: "Detected" },
  { key: "triaged", label: "Triaged" },
  { key: "investigated", label: "Investigated" },
  { key: "proposed", label: "Proposed fix" },
  { key: "guardrail", label: "Guardrail" },
  { key: "resolved", label: "Resolved" },
];

const RULE_TRACKER = [
  { key: "detected", label: "Detected" },
  { key: "rule", label: "Rule matched (no LLM)" },
  { key: "resolved", label: "Resolved" },
];

// Map an episode's raw step log onto a fixed set of named stages, so
// the UI can render a step tracker instead of a plain scrolling log.
export function deriveTracker(ep) {
  const usedRule = ep.steps.some((s) => s.stage === "RULE");
  const template = usedRule ? RULE_TRACKER : LLM_TRACKER;

  const find = (pred) => ep.steps.find(pred);
  const matchers = {
    triaged: (s) => s.stage === "AGENT" && s.text.startsWith("triage"),
    investigated: (s) => s.stage === "AGENT" && s.text.startsWith("investigate"),
    proposed: (s) => s.stage === "AGENT" && s.text.startsWith("propose"),
    guardrail: (s) => s.stage === "GUARD" || (s.stage === "ESCALATE" && !s.text.includes("quarantined")),
    rule: (s) => s.stage === "RULE",
    resolved: (s) => s.stage === "OK" || (s.stage === "ESCALATE" && s.text.includes("quarantined")),
  };

  return template.map((step) => {
    if (step.key === "detected") {
      return { ...step, done: true, text: ep.critical, resolved: null };
    }
    const match = find(matchers[step.key]);
    const isResolved = step.key === "resolved";
    return {
      ...step,
      done: Boolean(match) || (isResolved && ep.resolution != null),
      text: match?.text,
      resolved: isResolved ? ep.resolution : null,
    };
  });
}
