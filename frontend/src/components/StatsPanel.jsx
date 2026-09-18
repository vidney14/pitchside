import { Bar, BarChart, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const TEAM_COLORS = ["#38bdf8", "#fb923c"];
const TYPE_COLORS = ["#818cf8", "#10b981", "#f59e0b", "#22d3ee", "#f43f5e", "#a78bfa", "#34d399", "#fbbf24"];

export default function StatsPanel({ stats }) {
  if (!stats) {
    return (
      <div className="panel">
        <h2>Match Stats</h2>
        <div className="skeleton skeleton-lg" />
        <div className="skeleton" />
        <div className="skeleton" />
      </div>
    );
  }

  const teams = Object.entries(stats.by_team || {}).map(([team, count]) => ({ team, count }));
  const types = Object.entries(stats.by_event_type || {})
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(([type, count]) => ({ type, count }));

  return (
    <div className="panel">
      <h2>Match Stats</h2>
      <div className="stat-total">{stats.total_events} <span className="muted">events ingested</span></div>

      {teams.length > 0 && (
        <div className="stat-block">
          <h3>By team</h3>
          <ResponsiveContainer width="100%" height={70}>
            <BarChart data={teams} layout="vertical" margin={{ left: 0, right: 12, top: 0, bottom: 0 }}>
              <XAxis type="number" hide />
              <YAxis type="category" dataKey="team" width={64} tick={{ fill: "var(--text)", fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: "var(--bg-raised)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }} />
              <Bar dataKey="count" radius={[0, 5, 5, 0]} barSize={14}>
                {teams.map((t, i) => <Cell key={t.team} fill={TEAM_COLORS[i % TEAM_COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {types.length > 0 && (
        <div className="stat-block">
          <h3>Event types</h3>
          <div className="donut-row">
            <ResponsiveContainer width={90} height={90}>
              <PieChart>
                <Pie data={types} dataKey="count" nameKey="type" innerRadius={26} outerRadius={42} paddingAngle={2} strokeWidth={0}>
                  {types.map((t, i) => <Cell key={t.type} fill={TYPE_COLORS[i % TYPE_COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ background: "var(--bg-raised)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
            <div className="donut-legend">
              {types.map((t, i) => (
                <div className="legend-row" key={t.type}>
                  <span className="legend-dot" style={{ background: TYPE_COLORS[i % TYPE_COLORS.length] }} />
                  <span className="legend-label">{t.type}</span>
                  <span className="legend-value">{t.count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
