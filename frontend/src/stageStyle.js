// Colour-coding for bus stages. Kept in one place so the feed, the
// failures panel, the funnel chart, and the legend all agree.
// Grouped into the three semantic accents from index.css: healthy/OK
// (emerald), agent-working (indigo), critical/escalate (red/amber) --
// plus a couple of distinct hues for RULE (self-learned shortcut) and
// GUARD (the safety check) so those steps stay visually legible.
export const STAGE_COLORS = {
  OK: "#10b981",
  HEALED: "#10b981",
  INFO: "#64748b",
  AGENT: "#818cf8",
  GUARD: "#22d3ee",
  RULE: "#f59e0b",
  CRITICAL: "#fb923c",
  ESCALATE: "#f43f5e",
  FATAL: "#be123c",
};

export function stageColor(stage) {
  return STAGE_COLORS[stage] || "#64748b";
}
