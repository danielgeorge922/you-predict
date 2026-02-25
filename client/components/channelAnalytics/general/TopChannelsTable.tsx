import React from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { TOP_CHANNELS_DATA } from "@/consts/channelAnalyticsGeneral";

const TopChannelsTable = () => {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Channel</TableHead>
          <TableHead className="text-right">Subs</TableHead>
          <TableHead className="text-right">30d Growth</TableHead>
          <TableHead className="text-right">Views/Video (30d)</TableHead>
          <TableHead className="text-right">Engagement (30d)</TableHead>
          <TableHead className="text-right">Momentum</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {TOP_CHANNELS_DATA.map((row) => {
          const growthPositive = row.growth_30d.startsWith("+");
          return (
            <TableRow key={row.name} className="cursor-pointer">
              <TableCell className="font-medium">
                <div className="flex items-center gap-2">
                  <img
                    src={row.avatar}
                    alt={row.name}
                    className="w-7 h-7 rounded-full object-cover shrink-0"
                  />
                  {row.name}
                </div>
              </TableCell>
              <TableCell className="text-right">{row.subs}</TableCell>
              <TableCell
                className={`text-right ${growthPositive ? "text-green-600" : "text-red-500"}`}
              >
                {row.growth_30d}
              </TableCell>
              <TableCell className="text-right">{row.views_per_video}</TableCell>
              <TableCell className="text-right">{row.engagement}</TableCell>
              <TableCell className="text-right font-semibold">{row.momentum}</TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
};

export default TopChannelsTable;
