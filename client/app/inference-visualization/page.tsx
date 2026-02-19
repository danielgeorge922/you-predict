import React from "react";
import channels from "@/consts/channels";
import Image from "next/image";

const page = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-blue-100 rounded-full mb-6">
            <svg
              className="w-10 h-10 text-blue-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
          </div>
          <h2 className="text-3xl font-normal text-black mb-2">
            Choose a channel to get started
          </h2>
          <p className="text-gray-600 max-w-md mx-auto">
            View AI-powered predictions for video virality
    
          </p>
        </div>

        {/* Channel Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
          {channels.map((channel) => (
            <a
              key={channel.id}
              href={`/inference-visualization/${channel.id}`}
              className="group bg-white rounded-2xl p-6 shadow-sm hover:bg-blue-100 transition-colors duration-200"
            >
              <div className="flex items-center space-x-4">
                <div className="relative">
                  <Image
                    src={channel.pfp}
                    alt={channel.name}
                    className="w-16 h-16 rounded-full"
                    width={64}
                    height={64}
                  />
                  
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-medium text-gray-900">
                    {channel.name}
                  </h3>
                  <p className="text-sm text-gray-500 mt-1">View predictions</p>
                </div>
              </div>
            </a>
          ))}
        </div>

        {/* Footer CTA */}
        <div className="text-center mt-16 py-8 border-t border-gray-200">
          <p className="text-gray-500 text-sm">
            Powered by advanced machine learning algorithms
          </p>
        </div>
      </div>
    </div>
  );
};

export default page;
