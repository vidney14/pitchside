// Colour-coding for bus stages. Kept in one place so the feed, the
// failures panel, and any legend agree with each other.
export const STAGE_COLORS = {
  OK: "#2f9e58",
  INFO: "#5b7ba6",
  CRITICAL: "#d9822b",
  AGENT: "#7c5cd1",
  GUARD: "#1f9c93",
  HEALED: "#2f9e58",
  ESCALATE: "#d1435b",
  RULE: "#c98a1f",
  FATAL: "#8a1f2b",
};

export function stageColor(stage) {
  return STAGE_COLORS[stage] || "#888";
}
