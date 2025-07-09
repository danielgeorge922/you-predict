"use client";

import React from "react";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import { useRouter, usePathname } from "next/navigation";
import Image from "next/image";

const Header = () => {
  const router = useRouter();
  const pathname = usePathname();

  const routes = [
    { label: "Inference Visualization", href: "/inference-visualization" },
    { label: "Data Control", href: "/data-control" },
    { label: "Model Versioning", href: "/model-versioning" },
  ];

  const currentTab = routes.findIndex((route) =>
    pathname.startsWith(route.href)
  );
  const value = currentTab >= 0 ? currentTab : 0;

  return (
    <div className="flex-col">
      {/* Top White Half with the logo */}
      <div className="flex justify-between p-4">
        <div className="flex items-center">
          <Image src="/logo.svg" alt="logo" width={40} height={40} />
          <h1 className="ml-2 text-[20px] text-gray-600 font-light bg-white">
            YouPredict
          </h1>
        </div>

        {/* github link, with drop down for specific parts of repo (MLFlow, FrontEnd, anything else i wanna put on the right side) */}
        <div className="gap-4 flex items-center">
          <h1>github</h1>
          <h1>github</h1>
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
                fontWeight: 600,
                minHeight: "48px",
                fontFamily: "DM Sans, sans-serif",
                WebkitFontSmoothing: "antialiased",
                MozOsxFontSmoothing: "grayscale",
              }}
            />
          ))}
        </Tabs>
      </div>
    </div>
  );
};

export default Header;
