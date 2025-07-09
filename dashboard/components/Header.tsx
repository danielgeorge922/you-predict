"use client";

import React from "react";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import { useRouter, usePathname } from "next/navigation";

function samePageLinkNavigation(
  event: React.MouseEvent<HTMLAnchorElement, MouseEvent>
) {
  if (
    event.defaultPrevented ||
    event.button !== 0 || // ignore everything but left-click
    event.metaKey ||
    event.ctrlKey ||
    event.altKey ||
    event.shiftKey
  ) {
    return false;
  }
  return true;
}

interface LinkTabProps {
  label?: string;
  href?: string;
  selected?: boolean;
}

function LinkTab(props: LinkTabProps) {
  const router = useRouter();

  return (
    <Tab
      component="a"
      onClick={(event: React.MouseEvent<HTMLAnchorElement, MouseEvent>) => {
        event.preventDefault();
        if (props.href) {
          router.push(props.href);
        }
      }}
      aria-current={props.selected && "page"}
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
      {...props}
    />
  );
}

const Header = () => {
  const pathname = usePathname();

  const routes = [
    { label: "Inference Testing", href: "/inference-testing" },
    { label: "Data Control", href: "/data-control" },
    { label: "Model Versioning", href: "/model-versioning" },
  ];

  const currentTabIndex = routes.findIndex((route) =>
    pathname.startsWith(route.href)
  );
  const value = currentTabIndex >= 0 ? currentTabIndex : 0;

  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    // Tab change is now handled by individual LinkTab onClick
  };

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
          onChange={handleChange}
          aria-label="nav tabs example"
          role="navigation"
          sx={{
            "& .MuiTabs-indicator": {
              backgroundColor: "#ffffff",
              height: "3px",
            },
            "& .MuiTabs-root": {
              minHeight: "48px",
            },
          }}
        >
          {routes.map((route, index) => (
            <LinkTab
              key={route.href}
              label={route.label}
              href={route.href}
              selected={value === index}
            />
          ))}
        </Tabs>
      </div>
    </div>
  );
};

export default Header;
