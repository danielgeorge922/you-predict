"use client";

import channels from "@/consts/channels";
import Image from "next/image";
import React from "react";
import { usePathname } from "next/navigation";

const ChannelsSidebar = () => {
  const pathname = usePathname();
  const currentChannelId = pathname.split("/")[2]; // Extract ID from /inference-visualization/[id]

  return (
    <div className="bg-white border-r border-gray-200">
      <h2 className="px-4 mt-4 text-2xl">Channels</h2>
      <ul className="p-4">
        {channels.map((channel) => {
          const isActive = currentChannelId === channel.id.toString();

          return (
            <li key={channel.id}>
              <a
                href={`/inference-visualization/${channel.id}`}
                className={`flex items-center p-4 rounded-xl transition-colors ${
                  isActive ? "bg-blue-100 border-blue-500" : "hover:bg-gray-100"
                }`}
              >
                <Image
                  src={channel.pfp}
                  alt={channel.name}
                  className="w-10 h-10 rounded-full mr-4"
                  width={40}
                  height={40}
                />
                <span
                  className={`font-medium ${
                    isActive ? "text-blue-800" : "text-gray-700"
                  }`}
                >
                  {channel.name}
                </span>
              </a>
            </li>
          );
        })}
      </ul>
    </div>
  );
};

export default ChannelsSidebar;
