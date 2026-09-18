import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useLiveSeries } from "../useLiveSeries";

export default function LiveSeriesChart({ events }) {
  const series = useLiveSeries(events);
  const hasData = series.some((p) => p.rate > 0);

  return (
    <div className="panel live-series-panel">
      <div className="panel-header">
        <h2>Ingest rate</h2>
        <span className="muted">events / 0.5s, rolling window</span>
      </div>
      {!hasData ? (
        <div className="empty-state small">No events flowing yet.</div>
      ) : (
        <ResponsiveContainer width="100%" height={90}>
          <AreaChart data={series} margin={{ left: 0, right: 0, top: 6, bottom: 0 }}>
            <defs>
              <linearGradient id="rateFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--ok)" stopOpacity={0.35} />
                <stop offset="100%" stopColor="var(--ok)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="t" hide />
            <YAxis hide domain={[0, "auto"]} />
            <Tooltip
              contentStyle={{ background: "var(--bg-raised)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }}
              labelFormatter={() => ""}
              formatter={(value) => [value, "events"]}
            />
            <Area type="monotone" dataKey="rate" stroke="var(--ok)" strokeWidth={2} fill="url(#rateFill)" isAnimationActive={false} />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
