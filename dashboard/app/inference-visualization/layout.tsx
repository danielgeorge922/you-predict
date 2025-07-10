import ChannelsSidebar from "@/components/ChannelsSidebar";
import React from "react";

export default function InferenceVisualizationLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex">
      <ChannelsSidebar />
      <div className="flex-1">{children}</div>
    </div>
  );
}
