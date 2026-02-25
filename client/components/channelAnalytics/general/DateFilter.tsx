"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";

const OPTIONS = [
  { label: "7d", value: 7 },
  { label: "14d", value: 14 },
  { label: "30d", value: 30 },
];

const DateFilter = () => {
  const [selected, setSelected] = useState(7);

  return (
    <div className="flex gap-1">
      {OPTIONS.map((opt) => (
        <Button
          key={opt.value}
          size="sm"
          variant={selected === opt.value ? "default" : "outline"}
          onClick={() => setSelected(opt.value)}
        >
          {opt.label}
        </Button>
      ))}
    </div>
  );
};

export default DateFilter;
