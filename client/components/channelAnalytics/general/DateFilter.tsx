"use client";

import React from "react";
import { Button } from "@/components/ui/button";

const OPTIONS = [
  { label: "7d", value: 7 },
  { label: "14d", value: 14 },
  { label: "30d", value: 30 },
];

interface DateFilterProps {
  value: number;
  onChange: (days: number) => void;
}

const DateFilter = ({ value, onChange }: DateFilterProps) => {
  return (
    <div className="flex gap-1">
      {OPTIONS.map((opt) => (
        <Button
          key={opt.value}
          size="sm"
          variant={value === opt.value ? "default" : "outline"}
          onClick={() => onChange(opt.value)}
        >
          {opt.label}
        </Button>
      ))}
    </div>
  );
};

export default DateFilter;
