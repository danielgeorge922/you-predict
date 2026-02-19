"use client";
import ArrowForwardIosIcon from "@mui/icons-material/ArrowForwardIos";
import Image from "next/image";
import { useState, useEffect, use } from "react";
import { useRouter } from "next/navigation";
import channels from "@/consts/channels";
import dummyVideoData from "@/consts/videos";
import VideoCard, { VideoData } from "@/components/VideoCard";

interface ChannelData {
  id: number;
  name: string;
  pfp: string;
  url: string;
}

const TimeFilter = () => {
  const [selectedTime, setSelectedTime] = useState("24h");

  const timeOptions = [
    { value: "24h", label: "Last 24 Hours" },
    { value: "7d", label: "Last 7 Days" },
    { value: "30d", label: "Last 30 Days" },
    { value: "all", label: "All Time" },
  ];

  return (
    <select
      value={selectedTime}
      onChange={(e) => setSelectedTime(e.target.value)}
      className="px-3 py-2 border rounded-md text-sm"
    >
      {timeOptions.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
};

const InferenceVisualizationPage = ({
  params,
}: {
  params: Promise<{ id: string }>;
}) => {
  const [channelData, setChannelData] = useState<ChannelData | null>(null);
  const [filteredVideos, setFilteredVideos] = useState<VideoData[]>([]);
  const router = useRouter();

  // Use the React.use() hook to unwrap the Promise
  const resolvedParams = use(params);

  useEffect(() => {
    const channelId = parseInt(resolvedParams.id);
    const channel = channels.find((c) => c.id === channelId);
    setChannelData(channel || null);
    const channelVideos = dummyVideoData.filter(
      (video) => video.channel_id === channelId
    ) as VideoData[]; // assume that the type of the videos that we are sorting through is always type VideoData
    setFilteredVideos(channelVideos);
  }, [resolvedParams.id]);

  if (!channelData) {
    return <div className="p-8">Loading...</div>;
  }

  return (
    <div className="p-8 w-full">
      {/* Header */}
      <div className="flex justify-between items-center w-full mb-8">
        <div className="flex items-center">
          <button
            onClick={() => router.push("/inference-visualization")}
            className="text-gray-400 hover:text-gray-800 hover:cursor-pointer transition-colors"
          >
            <h1 className="text-[20px]">Channels</h1>
          </button>
          <ArrowForwardIosIcon className="mx-2 text-black text-sm" />
          <div className="flex items-center">
            <Image
              src={channelData.pfp}
              alt="Channel Logo"
              width={30}
              height={30}
              className="rounded-full mr-3"
            />
            <span className="text-[20px]">{channelData.name}</span>
          </div>
        </div>

        <TimeFilter />
      </div>

      {/* Video Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {filteredVideos.map((video) => (
          <VideoCard key={video.video_id} video={video} />
        ))}
      </div>
    </div>
  );
};

export default InferenceVisualizationPage;