"use client";

import React, { useState } from "react";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import { useRouter, usePathname } from "next/navigation";
import Image from "next/image";

const Header = () => {
  const router = useRouter();
  const pathname = usePathname();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [selectedVersion, setSelectedVersion] = useState("v1.2.3");

  const dataVersions = [
    { label: "v1.2.3", value: "v1.2.3" },
    { label: "v1.2.2", value: "v1.2.2" },
    { label: "v1.2.1", value: "v1.2.1" },
    { label: "v1.2.0", value: "v1.2.0" },
    { label: "v1.1.9", value: "v1.1.9" },
  ];

  const routes = [
    { label: "Inference Visualization", href: "/inference-visualization" },
    { label: "Model Performance", href: "/model-performance" },
    { label: "Model Monitoring", href: "/model-monitoring" },
  ];

  const currentTab = routes.findIndex((route) =>
    pathname.startsWith(route.href)
  );
  const value = currentTab >= 0 ? currentTab : false;

  const handleVersionSelect = (version: string) => {
    setSelectedVersion(version);
    setIsDropdownOpen(false);
  };

  const isRetrainEnabled = selectedVersion !== "v1.2.3";

  return (
    <div className="flex-col">
      {/* Top White Half with the logo */}
      <div className="flex justify-between px-8 p-4">
        <button
          onClick={() => router.push("/")}
          className="flex items-center hover:cursor-pointer"
        >
          <Image src="/Logo.svg" alt="logo" width={40} height={40} />
          <h1 className="ml-2 text-[20px] text-gray-600 transition-colors bg-white hover:text-black">
            YouPredict
          </h1>
        </button>

        {/* github link and design docs */}
        <div className="gap-4 flex items-center">
          <a
            href="https://github.com/danielgeorge922/you-predict"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors border border-gray-200"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
            </svg>
            <span className="text-sm font-medium">GitHub</span>
          </a>

          <a
            href="https://docs.google.com/document/d/your-doc-id"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors border border-gray-200"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M6 2c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6H6zm0 2h7v5h5v11H6V4zm2 8v2h8v-2H8zm0 4v2h8v-2H8z" />
            </svg>
            <span className="text-sm font-medium">Design Docs</span>
          </a>
        </div>
        <div className="flex items-center gap-4">
          {/* retrain model button */}
          <button
            disabled={!isRetrainEnabled}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors  text-sm font-medium ${
              isRetrainEnabled
                ? "bg-blue-100 text-blue-800 hover:bg-blue-200 hover:cursor-pointer"
                : "bg-gray-300 text-gray-500 border-gray-300 cursor-not-allowed"
            }`}
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 6v3l4-4-4-4v3c-4.42 0-8 3.58-8 8 0 1.57.46 3.03 1.24 4.26L6.7 14.8c-.45-.83-.7-1.79-.7-2.8 0-3.31 2.69-6 6-6zm6.76 1.74L17.3 9.2c.44.84.7 1.79.7 2.8 0 3.31-2.69 6-6 6v-3l-4 4 4 4v-3c4.42 0 8-3.58 8-8 0-1.57-.46-3.03-1.24-4.26z" />
            </svg>
            <span>Retrain Model</span>
          </button>

          {/* data versioning dropdown */}
          <div className="relative">
            <button
              onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors border border-gray-200 bg-white text-gray-700 text-sm font-medium min-w-[80px]"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
              </svg>
              <span>{selectedVersion}</span>
              <svg
                className={`w-4 h-4 transition-transform ${
                  isDropdownOpen ? "rotate-180" : ""
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </button>

            {isDropdownOpen && (
              <div className="absolute top-full left-0 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg z-50">
                {dataVersions.map((version) => (
                  <button
                    key={version.value}
                    onClick={() => handleVersionSelect(version.value)}
                    className={`w-full text-left px-3 py-2 hover:bg-gray-100 transition-colors first:rounded-t-lg last:rounded-b-lg text-sm ${
                      selectedVersion === version.value
                        ? "bg-blue-100 text-blue-800 font-medium hover:bg-blue-200"
                        : "text-gray-700"
                    }`}
                  >
                    {version.label}
                  </button>
                ))}
              </div>
            )}
          </div>

          <Image
            src="/Daniel.png"
            alt="Profile"
            width={32}
            height={32}
            className="rounded-full cursor-pointer hover:opacity-80 transition-opacity border ring-4 ring-[#FF0000]"
          />
        </div>
      </div>

      {/* Bottom Red Half with the white tabs */}
      <div className="flex justify-start shadow-md items-center bg-[#FF0000] h-12">
        <Tabs
          value={value}
          aria-label="nav tabs example"
          sx={{
            "& .MuiTabs-indicator": {
              backgroundColor: "#ffffff",
              height: "3px",
            },
          }}
        >
          {routes.map((route) => (
            <Tab
              key={route.href}
              label={route.label}
              onClick={() => router.push(route.href)}
              sx={{
                color: "rgba(255, 255, 255, 0.7)",
                "&:hover": {
                  color: "rgba(255, 255, 255, 0.9)",
                },
                "&.Mui-selected": {
                  color: "#ffffff",
                  backgroundColor: "rgba(255, 255, 255, 0.1)",
                },
                textTransform: "none",
                fontSize: "14px",
                fontWeight: 500,
                minHeight: "48px",
                WebkitFontSmoothing: "antialiased",
                MozOsxFontSmoothing: "grayscale",
                fontFamily: "Poppins, sans-serif",
              }}
            />
          ))}
        </Tabs>
      </div>
    </div>
  );
};

export default Header;
