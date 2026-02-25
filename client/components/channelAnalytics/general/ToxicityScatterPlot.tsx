"use client";

import React from "react";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts";
import { TOXICITY_SCATTER_DATA, ToxicityScatterPoint } from "@/consts/channelAnalyticsGeneral";

const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: { payload: ToxicityScatterPoint }[] }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="rounded-lg border bg-background p-2 text-xs shadow-md">
      <p className="font-semibold">{d.channel}</p>
      <p>Perf: <span className="font-medium">{d.perf.toFixed(2)}x</span></p>
      <p>Toxicity: <span className="font-medium">{(d.toxicity * 100).toFixed(0)}%</span></p>
      <p>Comments: <span className="font-medium">{d.comments}</span></p>
    </div>
  );
};

const ToxicityScatterPlot = () => {
  return (
    <ResponsiveContainer width="100%" height={320}>
      <ScatterChart margin={{ top: 8, right: 24, bottom: 8, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="perf"
          name="Performance"
          type="number"
          domain={[0, 2.5]}
          tickFormatter={(v) => `${v}x`}
          tick={{ fontSize: 11 }}
          label={{ value: "perf vs channel avg", position: "insideBottom", offset: -2, fontSize: 10 }}
        />
        <YAxis
          dataKey="toxicity"
          name="Toxicity"
          type="number"
          domain={[0, 0.6]}
          tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
          tick={{ fontSize: 11 }}
          label={{ value: "toxic ratio", angle: -90, position: "insideLeft", offset: 8, fontSize: 10 }}
        />
        <Tooltip content={<CustomTooltip />} />
        <ReferenceLine x={1} stroke="hsl(var(--muted-foreground))" strokeDasharray="4 2" />
        <Scatter
          data={TOXICITY_SCATTER_DATA}
          fill="hsl(var(--primary))"
          fillOpacity={0.7}
        />
      </ScatterChart>
    </ResponsiveContainer>
  );
};

export default ToxicityScatterPlot;
