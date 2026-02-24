"use client";

import WarningToast from "@/components/WarningToast";
import TechStackModal from "@/components/TechStackModal";
import { techStack, whyReasonSections } from "@/consts/mainpage";
import Image from "next/image";
import React, { useState } from "react";

const Page = () => {
  const [selectedTech, setSelectedTech] = useState<{
    name: string;
    icon: string;
    description: string;
  } | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const openModal = (tech: {
    name: string;
    icon: string;
    description: string;
  }) => {
    setSelectedTech(tech);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedTech(null);
  };

  return (
    <div className="w-full min-h-screen flex justify-center px-4">
      <div className="w-full max-w-7xl rounded-xl p-8 gap-4">
        <WarningToast />
        <div className="mt-4 flex flex-col gap-4">
          <h1 className="text-[56px]">YouPredict</h1>

          <h1 className="text-[20px] text-gray-600">
            A portfolio project that showcases my passion for MLOps, data
            visualization, and front-end development. It is designed to provide
            insights into YouTube video virality using machine learning models.
          </h1>
        </div>

        {/* MIDDLE PART WITH THE IMAGE AND THEN TO THE RIGHT SOMETHING ELSE (75% image) and then 25% text */}
        <div className="flex mt-16 gap-6">
          <div className="w-3/4">
            <div className="relative w-full h-[400px] bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl overflow-hidden border border-gray-200">
              <Image
                src="/images/YT.png"
                alt="YouPredict Dashboard Preview"
                fill
                className="object-cover"
                priority
              />
            </div>
          </div>
          <div className="w-1/4 flex flex-col justify-center">
            <div className="space-y-4">
              <button className="w-full py-3 px-4 bg-[#FF0000] text-white rounded-lg hover:bg-[#EE0000] hover:cursor-pointer transition-colors">
                Try YouPredict
              </button>
              <button className="w-full py-3 px-4 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">
                View Code
              </button>
            </div>
          </div>
        </div>

        {/* WHAT THIS IS SECTION */}
        <div className="mt-20">
          <h2 className="text-[40px] font-semibold mb-6">Why</h2>
          <p className="text-gray-600 text-[20px] mt-4">
            YouPredict is meant to simulate how a real-world{" "}
            <strong className="text-black">MLOps</strong> project would look
            like, with a focus on{" "}
            <strong className="text-black">data visualization</strong> and{" "}
            <strong className="text-black">model performance monitoring</strong>
            . It is designed to provide insights into YouTube video virality
            using machine learning models.
          </p>
          <p className="mt-2 text-gray-600">
            Here are <strong className="text-black">3 key reasons</strong> why
            companies would benefit from a production-ready tool like this:
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 w-full mt-4">
            {whyReasonSections.map((section, index) => (
              <div key={index} className="p-4 rounded-lg">
                <h3 className="text-[20px] mb-2">
                  {index + 1}. {section.title}
                </h3>
                <Image
                  src={section.graphic}
                  alt={section.title}
                  width={500}
                  height={400}
                  className="w-full object-cover rounded-lg mb-4"
                />
                <p className="text-gray-600 text-[16px]">
                  {section.description}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* TECH STACK SECTION */}
        <div className="mt-16 mb-16">
          <h2 className="text-[40px] font-semibold mb-6">Tech Stack</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {techStack.map((tech, index) => (
              <div
                key={index}
                className="bg-white border border-gray-200 rounded-lg p-6 text-center hover:shadow-sm transition-shadow relative"
              >
                <button
                  onClick={() => openModal(tech)}
                  className="absolute top-2 right-2 w-6 h-6 bg-gray-100 hover:bg-gray-200 rounded-full flex items-center justify-center text-gray-600 hover:text-gray-800 transition-colors text-sm"
                  title={`Learn more about ${tech.name}`}
                >
                  i
                </button>
                <div className="flex flex-col items-center gap-3">
                  <Image
                    src={tech.icon}
                    alt={tech.name}
                    width={40}
                    height={40}
                    className="w-12 h-12"
                  />
                  <span className="text-gray-700 font-medium text-[16px]">
                    {tech.name}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <TechStackModal
          isOpen={isModalOpen}
          onClose={closeModal}
          tech={selectedTech}
        />
      </div>
    </div>
  );
};

export default Page;
