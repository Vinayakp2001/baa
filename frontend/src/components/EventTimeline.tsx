import { EventOut } from "@/lib/api";
import { Badge } from "@/components/ui/badge";

const EVENT_COLORS: Record<string, string> = {
  BUSINESS_DISCOVERED: "success",
  BUSINESS_UPDATED: "secondary",
  STATUS_CHANGED: "warning",
  NAME_CHANGED: "warning",
  LOCATION_CHANGED: "secondary",
  FEDERAL_INCORPORATION: "default",
  PROVINCIAL_REGISTRATION: "default",
  MUNICIPAL_LICENCE_FIRST_ISSUE: "default",
  MUNICIPAL_PERMIT_ISSUED: "secondary",
  LICENCE_STATUS_CHANGE: "warning",
};

export function EventTimeline({ events }: { events: EventOut[] }) {
  const sorted = [...events].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  return (
    <div className="space-y-3">
      {sorted.map((ev) => (
        <div key={ev.event_id} className="flex gap-4 text-sm">
          <div className="flex flex-col items-center">
            <div className="h-2.5 w-2.5 rounded-full bg-primary mt-0.5" />
            <div className="w-px flex-1 bg-border mt-1" />
          </div>
          <div className="pb-3 flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <Badge variant={(EVENT_COLORS[ev.event_type] ?? "secondary") as "success" | "warning" | "secondary" | "default"}>
                {ev.event_type}
              </Badge>
              {ev.event_date && (
                <span className="text-muted-foreground text-xs">{ev.event_date}</span>
              )}
              <span className="text-muted-foreground text-xs ml-auto">
                {new Date(ev.created_at).toLocaleDateString("en-CA")}
              </span>
            </div>
            {ev.raw_value && (
              <p className="text-xs text-muted-foreground mt-1">
                {ev.previous_value ? (
                  <><span className="line-through">{ev.previous_value}</span> → {ev.raw_value}</>
                ) : ev.raw_value}
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
