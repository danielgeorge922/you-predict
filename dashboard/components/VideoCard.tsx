import Image from "next/image";

export interface VideoData {
  video_id: string;
  channel_id: number;
  title: string;
  uploadedAt: string;
  currentViewCount: number;
  predictedClassification: "underperforming" | "average" | "viral";
  actualClassification?: "underperforming" | "average" | "viral"; // undefined if too recent to tell
  wasCorrect: 0 | 1 | 2; // 0: wrong, 1: correct, 2: too recent to tell
  thumbnail: {
    url: string;
    width: number;
    height: number;
  };
}

const VideoCard = ({ video }: { video: VideoData }) => {
  const getBadgeColor = (wasCorrect: number) => {
    switch (wasCorrect) {
      case 1:
        return "bg-green-500"; // Correct
      case 0:
        return "bg-red-500"; // Wrong
      default:
        return "bg-gray-400"; // Too recent
    }
  };

  const getBadgeIcon = (wasCorrect: number) => {
    switch (wasCorrect) {
      case 1:
        return "✓";
      case 0:
        return "✗";
      default:
        return "?";
    }
  };

  const getClassificationColor = (classification: string) => {
    switch (classification) {
      case "viral":
        return "text-green-600 bg-green-50";
      case "average":
        return "text-yellow-600 bg-yellow-50";
      case "underperforming":
        return "text-red-600 bg-red-50";
      default:
        return "text-gray-600 bg-gray-50";
    }
  };

  const formatViewCount = (count: number) => {
    if (count >= 1000000) return `${(count / 1000000).toFixed(1)}M`;
    if (count >= 1000) return `${(count / 1000).toFixed(1)}K`;
    return count.toString();
  };

  const formatClassification = (classification: string) => {
    return classification.charAt(0).toUpperCase() + classification.slice(1);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  return (
    <div className="bg-white rounded-2xl shadow-md overflow-hidden relative">
      {/* Prediction Badge */}
      <div
        className={`absolute top-2 right-2 ${getBadgeColor(
          video.wasCorrect
        )} text-white text-xs px-2 py-1 rounded-full z-10`}
      >
        {getBadgeIcon(video.wasCorrect)}
      </div>

      <Image
        src={video.thumbnail.url}
        alt={video.title}
        width={video.thumbnail.width}
        height={video.thumbnail.height}
        className="w-full h-48 object-cover rounded-2xl"
      />

      <div className="p-4">
        <h3 className="text-md mb-2 line-clamp-2">{video.title}</h3>
        <div className="text-xs space-y-2">
          {/* Views and Date Row */}
          <div className="flex justify-between items-center">
            <p className="text-gray-600">
              {formatViewCount(video.currentViewCount)} Views
            </p>
            <p className="text-gray-600">{formatDate(video.uploadedAt)}</p>
          </div>

          {/* Predicted Classification */}
          <div className="flex items-center gap-2">
            <span className="text-gray-500">Predicted:</span>
            <span
              className={`px-2 py-1 rounded-full text-xs font-medium ${getClassificationColor(
                video.predictedClassification
              )}`}
            >
              {formatClassification(video.predictedClassification)}
            </span>
          </div>

          {/* Actual Classification */}
          {video.actualClassification ? (
            <div className="flex items-center gap-2">
              <span className="text-gray-500">Actual:</span>
              <span
                className={`px-2 py-1 rounded-full text-xs font-medium ${getClassificationColor(
                  video.actualClassification
                )}`}
              >
                {formatClassification(video.actualClassification)}
              </span>
            </div>
          ) : (
            <p className="text-gray-400 text-xs">
              Actual: Too recent to determine
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default VideoCard;
