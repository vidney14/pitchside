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
