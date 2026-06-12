import * as React from "react";
import { Severity } from "../modules/RedFlagItem";

interface TimelineEvent {
  id: string;
  year: string; // e.g., "Jan 2022"
  label: string;
  severity: Severity;
}

interface RedFlagTimelineProps {
  events: TimelineEvent[];
}

export function RedFlagTimeline({ events }: RedFlagTimelineProps) {
  const dotColors = {
    severe: "bg-risk-severe",
    high: "bg-risk-high",
    moderate: "bg-risk-moderate",
  };
  
  const tickColors = {
    severe: "bg-risk-severe",
    high: "bg-risk-high",
    moderate: "bg-risk-moderate",
  };

  return (
    <div className="relative w-full overflow-hidden after:content-[''] after:absolute after:right-0 after:top-0 after:bottom-0 after:w-[48px] after:bg-gradient-to-r after:from-transparent after:to-canvas after:pointer-events-none after:z-10">
      <div className="overflow-x-auto pb-16 pt-24 no-scrollbar">
        <div className="relative min-w-[600px] flex items-end">
          {/* Baseline */}
          <div className="absolute bottom-[28px] left-0 right-0 h-[1px] bg-border" />
          
          <div className="flex justify-between w-full px-4 relative z-0">
            {events.map((event, index) => (
              <div key={event.id} className="flex flex-col items-center relative w-24">
                {/* Event Label (rotated) */}
                <div className="absolute bottom-[60px] left-1/2 -translate-x-1/2 -rotate-30 transform origin-bottom-left whitespace-nowrap text-[11px] text-text-primary font-sans w-24">
                  {event.label}
                </div>
                
                {/* Dot */}
                <div className={`absolute bottom-[48px] w-2 h-2 rounded-full z-10 ${dotColors[event.severity]}`} />
                
                {/* Tick */}
                <div className={`absolute bottom-[28px] w-[1px] h-[20px] ${tickColors[event.severity]}`} />
                
                {/* Year Marker */}
                <div className="absolute bottom-0 text-[11px] text-text-secondary font-mono">
                  {event.year}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
