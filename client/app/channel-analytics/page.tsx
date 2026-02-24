import React from "react";

const ChannelAnalyticsPage = () => {
  return (
    <div className="p-8 w-full">
      <h1 className="text-3xl font-normal text-black mb-2">Channel Analytics</h1>
      <p className="text-gray-600 mb-12">
        What drives virality across tracked channels?
      </p>

      {/* Channel Benchmarks */}
      <section className="mb-12">
        <h2 className="text-xl font-medium mb-4">Channel Benchmarks</h2>
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <p className="text-gray-400 text-sm">Sortable table coming soon</p>
        </div>
      </section>

      {/* Best Time to Post */}
      <section className="mb-12">
        <h2 className="text-xl font-medium mb-4">Best Time to Post</h2>
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <p className="text-gray-400 text-sm">Posting heatmap coming soon</p>
        </div>
      </section>

      {/* View Velocity Curves */}
      <section className="mb-12">
        <h2 className="text-xl font-medium mb-4">View Velocity Curves</h2>
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <p className="text-gray-400 text-sm">72h velocity chart coming soon</p>
        </div>
      </section>
    </div>
  );
};

export default ChannelAnalyticsPage;
