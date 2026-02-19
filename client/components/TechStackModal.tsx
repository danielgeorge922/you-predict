import Image from "next/image";
import React from "react";

interface TechStackModalProps {
  isOpen: boolean;
  onClose: () => void;
  tech: {
    name: string;
    icon: string;
    description: string;
  } | null;
}

const TechStackModal: React.FC<TechStackModalProps> = ({
  isOpen,
  onClose,
  tech,
}) => {
  if (!isOpen || !tech) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl max-w-md w-full p-6 relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 text-xl"
        >
          ×
        </button>
        
        <div className="flex items-center gap-4 mb-4">
          <Image
            src={tech.icon}
            alt={tech.name}
            width={48}
            height={48}
            className="w-12 h-12"
          />
          <h3 className="text-2xl font-semibold text-gray-800">{tech.name}</h3>
        </div>
        
        <p className="text-gray-600 leading-relaxed">{tech.description}</p>
      </div>
    </div>
  );
};

export default TechStackModal;