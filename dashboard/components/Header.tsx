"use client";

import React from "react";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import { useRouter, usePathname } from "next/navigation";

const Header = () => {
  const router = useRouter();
  const pathname = usePathname();

  const routes = [
    { label: "Inference Testing", href: "/inference-testing" },
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
      <div>
        <h1 className="text-[20px] text-gray-600 p-4 font-light w-full bg-white">
          YouPredict
        </h1>
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
                fontWeight: 400,
                minHeight: "48px",
                fontFamily:
                  "Montserrat, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
              }}
            />
          ))}
        </Tabs>
      </div>
    </div>
  );
};

export default Header;
