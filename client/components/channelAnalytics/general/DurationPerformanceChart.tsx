"use client";

import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts";
import { DURATION_PERFORMANCE_DATA } from "@/consts/channelAnalyticsGeneral";

const DurationPerformanceChart = () => {
  return (
    <ResponsiveContainer width="100%" height={288}>
      <BarChart
        data={DURATION_PERFORMANCE_DATA}
        layout="vertical"
        margin={{ top: 4, right: 24, bottom: 4, left: 8 }}
      >
        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
        <XAxis
          type="number"
          domain={[0, 2]}
          tickFormatter={(v) => `${v}x`}
          tick={{ fontSize: 11 }}
        />
        <YAxis
          type="category"
          dataKey="bucket"
          width={44}
          tick={{ fontSize: 11 }}
        />
        <Tooltip
          formatter={(value: number) => [`${value.toFixed(2)}x`, "Median perf vs channel avg"]}
          cursor={{ fill: "hsl(var(--muted))" }}
        />
        <ReferenceLine x={1} stroke="hsl(var(--muted-foreground))" strokeDasharray="4 2" />
        <Bar dataKey="median_perf" fill="hsl(var(--primary))" radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
};

export default DurationPerformanceChart;
