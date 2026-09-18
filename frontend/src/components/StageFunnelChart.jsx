import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { stageColor } from "../stageStyle";

const ORDER = ["OK", "CRITICAL", "AGENT", "GUARD", "RULE", "HEALED", "ESCALATE", "FATAL"];

export default function StageFunnelChart({ byStage }) {
  const data = ORDER
    .filter((stage) => byStage?.[stage])
    .map((stage) => ({ stage, count: byStage[stage] }));

  return (
    <div className="panel funnel-panel">
      <div className="panel-header">
        <h2>What the agent actually did</h2>
        <span className="muted">audit log, by pipeline stage</span>
      </div>
      {(!byStage || data.length === 0) ? (
        <div className="empty-state">No activity yet — start a run to populate this.</div>
      ) : (
        <ResponsiveContainer width="100%" height={Math.max(160, data.length * 34)}>
          <BarChart data={data} layout="vertical" margin={{ left: 8, right: 24, top: 4, bottom: 4 }}>
            <XAxis type="number" hide />
            <YAxis
              type="category" dataKey="stage" width={80}
              tick={{ fill: "var(--text)", fontSize: 12, fontFamily: "var(--mono)" }}
              axisLine={false} tickLine={false}
            />
            <Tooltip
              cursor={{ fill: "rgba(255,255,255,0.04)" }}
              contentStyle={{ background: "var(--bg-raised)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }}
              labelStyle={{ color: "var(--text-h)" }}
            />
            <Bar dataKey="count" radius={[0, 6, 6, 0]} barSize={16}>
              {data.map((d) => <Cell key={d.stage} fill={stageColor(d.stage)} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
