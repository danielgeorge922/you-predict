import WarningToast from "@/components/WarningToast";
import { techStack, whyReasonSections } from "@/consts/mainpage";
import Image from "next/image";
import React from "react";

const page = () => {
  return (
    <div className="w-full min-h-screen flex justify-center px-4">
      <div className="w-full max-w-7xl rounded-xl p-8 gap-4">
        <WarningToast />
        <div className="mt-4 flex flex-col gap-4">
          <h1 className="text-[40px]">YouPredict</h1>

          <h1 className="text-[20px] text-gray-600">
            A portfolio project that showcases my passion for MLOps, data
            visualization, and front-end development. It is designed to provide
            insights into YouTube video virality using machine learning models.
          </h1>
        </div>

        {/* MIDDLE PART WITH THE IMAGE AND THEN TO THE RIGHT SOMETHING ELSE (75% image) and then 25% text */}
        <div className="flex mt-16 gap-6">
          <div className="w-3/4">
            <button className="w-full h-[400px] bg-red-100 rounded-xl"></button>
          </div>
          <div className="w-1/4 flex flex-col justify-center">
            <div className="space-y-4">
              <div className="text-gray-600 text-sm">Live Demo</div>
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
          <h2 className="text-[32px] font-semibold mb-6">Why</h2>
          <p className="text-gray-600 mt-4">
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
                <h3 className="text-lg mb-2">
                  {index + 1}. {section.title}
                </h3>
                <Image
                  src={section.graphic}
                  alt={section.title}
                  width={500}
                  height={400}
                  className="w-full object-cover rounded-lg mb-4"
                />
                <p className="text-gray-600">{section.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* HOW SECTION */}
        <div className="mt-16">
          <h2 className="text-[32px] font-semibold mb-6">How</h2>
          <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl p-8">
            <div className="mb-6">
              <h3 className="text-xl font-medium mb-4">
                Technical Architecture
              </h3>
              <div className="bg-white rounded-lg p-6 min-h-[150px]">
                <p className="text-gray-500 text-center mt-12">
                  [Space for discussing the gradient boosting model, data
                  pipeline, and technical implementation details]
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
              <div className="bg-white rounded-lg p-6">
                <h4 className="font-medium mb-3 text-gray-800">
                  Machine Learning Stack
                </h4>
                <div className="text-gray-500 min-h-[100px]">
                  [Space for ML framework details, model training, and
                  evaluation metrics]
                </div>
              </div>
              <div className="bg-white rounded-lg p-6">
                <h4 className="font-medium mb-3 text-gray-800">
                  Infrastructure & Deployment
                </h4>
                <div className="text-gray-500 min-h-[100px]">
                  [Space for deployment strategy, scaling considerations, and
                  infrastructure choices]
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* TECH STACK SECTION */}
        <div className="mt-16 mb-16">
          <h2 className="text-[32px] font-semibold mb-6">Tech Stack</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {techStack.map((tech, index) => (
              <div
                key={index}
                className="bg-white border border-gray-200 rounded-lg p-6 text-center hover:shadow-sm transition-shadow"
              >
                <div className="flex flex-col items-center gap-3">
                  <Image
                    src={tech.icon}
                    alt={tech.name}
                    width={32}
                    height={32}
                    className="w-8 h-8"
                  />
                  <span className="text-gray-700 font-medium text-sm">{tech.name}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default page;
