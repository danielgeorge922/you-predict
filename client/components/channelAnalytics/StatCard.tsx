import React from "react";

export interface StatCardProps {
  title: string;
  value: string | number;
  change: string; // e.g. "vs prior day" or "across all channels"
}

const StatCard = ({ title, value, change }: StatCardProps) => {
  return (
    <div className="bg-white rounded-xl shadow-xs p-4">
      <p className="text-sm text-muted-foreground">{title}</p>
      <p className="text-2xl font-semibold">{value}</p>
      <p className="text-xs text-muted-foreground">{change}</p>
    </div>
  );
};

export default StatCard;
