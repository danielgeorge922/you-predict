import ChannelsSidebar from "@/components/ChannelsSidebar";

export default function ChannelAnalyticsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex">
      <ChannelsSidebar basePath="/channel-analytics" />
      <div className="flex-1">{children}</div>
    </div>
  );
}
