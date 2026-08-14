"use client";

import { useMemo } from "react";
import { cn } from "@/lib/utils";
import type { ActivityDayOut } from "@/types/api";

const MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const DAY_ROW_LABELS = ["", "Mon", "", "Wed", "", "Fri", ""];
const CELL = 11;
const GAP = 3;
const COL_STEP = CELL + GAP;

function intensityClass(count: number): string {
  if (count <= 0) return "bg-surface-muted";
  if (count <= 2) return "bg-brand/30";
  if (count <= 5) return "bg-brand/55";
  if (count <= 9) return "bg-brand/80";
  return "bg-brand";
}

interface DayCell {
  date: string;
  inYear: boolean;
  count: number;
}

interface ActivityHeatmapProps {
  year: number;
  data: ActivityDayOut[];
  selectedDate: string | null;
  onSelectDay: (date: string) => void;
}

export function ActivityHeatmap({ year, data, selectedDate, onSelectDay }: ActivityHeatmapProps) {
  const countByDate = useMemo(() => {
    const map = new Map<string, number>();
    for (const d of data) map.set(d.date, d.count);
    return map;
  }, [data]);

  const { weeks, monthMarkers } = useMemo(() => {
    const start = new Date(Date.UTC(year, 0, 1));
    const gridStart = new Date(start);
    gridStart.setUTCDate(gridStart.getUTCDate() - start.getUTCDay());

    const end = new Date(Date.UTC(year, 11, 31));
    const gridEnd = new Date(end);
    gridEnd.setUTCDate(gridEnd.getUTCDate() + (6 - end.getUTCDay()));

    const weeksArr: DayCell[][] = [];
    const monthMarkersArr: { weekIndex: number; label: string }[] = [];
    const cursor = new Date(gridStart);
    let weekIndex = 0;
    let lastMonth = -1;

    while (cursor <= gridEnd) {
      const week: DayCell[] = [];
      for (let i = 0; i < 7; i++) {
        const iso = cursor.toISOString().slice(0, 10);
        const inYear = cursor.getUTCFullYear() === year;
        if (inYear && cursor.getUTCMonth() !== lastMonth && cursor.getUTCDate() <= 7) {
          monthMarkersArr.push({ weekIndex, label: MONTH_LABELS[cursor.getUTCMonth()] });
          lastMonth = cursor.getUTCMonth();
        }
        week.push({ date: iso, inYear, count: countByDate.get(iso) ?? 0 });
        cursor.setUTCDate(cursor.getUTCDate() + 1);
      }
      weeksArr.push(week);
      weekIndex++;
    }
    return { weeks: weeksArr, monthMarkers: monthMarkersArr };
  }, [year, countByDate]);

  return (
    <div className="overflow-x-auto pb-1">
      <div className="inline-block min-w-full">
        <div className="relative mb-1 h-4" style={{ marginLeft: 24 }}>
          {monthMarkers.map((m, i) => (
            <span key={i} className="absolute text-[10px] text-muted" style={{ left: m.weekIndex * COL_STEP }}>
              {m.label}
            </span>
          ))}
        </div>
        <div className="flex gap-[3px]">
          <div className="flex flex-col gap-[3px] pr-1" style={{ width: 20 }}>
            {DAY_ROW_LABELS.map((l, i) => (
              <span key={i} className="h-[11px] text-[9px] leading-[11px] text-muted">
                {l}
              </span>
            ))}
          </div>
          {weeks.map((week, wi) => (
            <div key={wi} className="flex flex-col gap-[3px]">
              {week.map((day) => (
                <button
                  key={day.date}
                  type="button"
                  disabled={!day.inYear}
                  onClick={() => onSelectDay(day.date)}
                  title={`${day.date}: ${day.count} question${day.count === 1 ? "" : "s"} solved`}
                  aria-label={`${day.date}: ${day.count} questions solved`}
                  className={cn(
                    "rounded-[2px] transition-transform hover:scale-125 focus-visible:scale-125 focus-visible:outline-none",
                    day.inYear ? intensityClass(day.count) : "bg-transparent",
                    selectedDate === day.date && "ring-2 ring-brand ring-offset-1 ring-offset-background",
                  )}
                  style={{ height: CELL, width: CELL }}
                />
              ))}
            </div>
          ))}
        </div>
      </div>
      <div className="mt-2 flex items-center gap-1.5 text-[10px] text-muted">
        <span>Less</span>
        {[0, 2, 5, 9, 12].map((n) => (
          <span key={n} className={cn("rounded-[2px]", intensityClass(n))} style={{ height: CELL, width: CELL }} />
        ))}
        <span>More</span>
      </div>
    </div>
  );
}
