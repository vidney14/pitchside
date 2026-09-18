function Tile({ label, value, accent }) {
  return (
    <div className="stat-tile">
      <div className="stat-tile-value" style={accent ? { color: accent } : undefined}>
        {value}
      </div>
      <div className="stat-tile-label">{label}</div>
    </div>
  );
}

export default function StatTiles({ eventsIngested, healed, escalated, rulesLearned }) {
  return (
    <div className="stat-tile-row">
      <Tile label="Events ingested" value={eventsIngested} />
      <Tile label="Failures healed" value={healed} accent="var(--ok)" />
      <Tile label="Escalations" value={escalated} accent="var(--danger)" />
      <Tile label="Rules learned" value={rulesLearned} accent="var(--agent)" />
    </div>
  );
}
