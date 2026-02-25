import STAT_CARDS from "@/consts/channelAnalyticsGeneral";
import StatCard from "@/components/channelAnalytics/StatCard";
import DurationPerformanceChart from "@/components/channelAnalytics/general/DurationPerformanceChart";
import TopChannelsTable from "@/components/channelAnalytics/general/TopChannelsTable";
import ToxicityScatterPlot from "@/components/channelAnalytics/general/ToxicityScatterPlot";
import BiggestMoversTable from "@/components/channelAnalytics/general/BiggestMoversTable";
import DateFilter from "@/components/channelAnalytics/general/DateFilter";
import React from "react";

const ChannelAnalyticsPage = () => {
  return (
    <div className="p-8 w-full space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Channel Analytics</h1>
          <p className="text-sm text-muted-foreground">
            All channels overview — trends, leaders, and cross-channel patterns.
          </p>
        </div>
        <DateFilter />
      </div>

      {/* Row 1: 4 Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {STAT_CARDS.map((card) => (
          <StatCard
            key={card.label}
            title={card.label}
            value={card.value}
            change={card.sub}
          />
        ))}
      </div>

      {/* Row 2: Duration vs Performance + Top Channels table */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <div className="rounded-xl p-4 lg:col-span-2 bg-white">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">
              What Works: Duration vs Performance
            </h2>
            <span className="text-xs text-muted-foreground">
              median perf vs channel avg
            </span>
          </div>
          <DurationPerformanceChart />
          <p className="mt-3 text-xs text-muted-foreground">
            Across all channels, this duration band tends to outperform.
          </p>
        </div>

        <div className="rounded-xl p-4 lg:col-span-3 bg-white">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">
              Top Channels (30d Momentum)
            </h2>
            <span className="text-xs text-muted-foreground">
              ml_feature_channel · latest computed_date
            </span>
          </div>
          <TopChannelsTable />
          <p className="mt-3 text-xs text-muted-foreground">
            Click a row to navigate to channel-specific analytics.
          </p>
        </div>
      </div>

      {/* Row 3: Toxicity vs Performance scatter + Biggest Movers */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <div className="rounded-xl p-4 lg:col-span-3 bg-white">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">
              Audience Reaction: Toxicity vs Performance
            </h2>
            <span className="text-xs text-muted-foreground">
              videos · 72h window
            </span>
          </div>
          <ToxicityScatterPlot />
          <p className="mt-3 text-xs text-muted-foreground">
            Does toxic commentary correlate with better or worse performance?
          </p>
        </div>

        <div className="rounded-xl p-4 lg:col-span-2 bg-white">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">
              Biggest Movers (Yesterday)
            </h2>
            <span className="text-xs text-muted-foreground">
              fact_channel_snapshot · latest snapshot_date
            </span>
          </div>
          <BiggestMoversTable />
          <p className="mt-3 text-xs text-muted-foreground">
            What changed since yesterday?
          </p>
        </div>
      </div>
    </div>
  );
};

export default ChannelAnalyticsPage;
