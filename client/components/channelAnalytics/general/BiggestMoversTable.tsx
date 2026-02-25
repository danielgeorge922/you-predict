import React from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { BIGGEST_MOVERS_DATA } from "@/consts/channelAnalyticsGeneral";

const BiggestMoversTable = () => {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Channel</TableHead>
          <TableHead className="text-right">Views Δ</TableHead>
          <TableHead className="text-right">Subs Δ</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {BIGGEST_MOVERS_DATA.map((row) => (
          <TableRow key={row.channel}>
            <TableCell className="font-medium">
                <div className="flex items-center gap-2">
                  <img
                    src={row.avatar}
                    alt={row.channel}
                    className="w-7 h-7 rounded-full object-cover shrink-0"
                  />
                  {row.channel}
                </div>
              </TableCell>
            <TableCell
              className={`text-right ${row.views_positive ? "text-green-600" : "text-red-500"}`}
            >
              {row.views_delta}
            </TableCell>
            <TableCell
              className={`text-right ${row.subs_positive ? "text-green-600" : "text-red-500"}`}
            >
              {row.subs_delta}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};

export default BiggestMoversTable;
