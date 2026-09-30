import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ExportButton } from "@/components/ExportButton";

export const revalidate = 120;

export default async function SourcesPage() {
  let sources;
  try {
    sources = await api.sources.list();
  } catch {
    sources = null;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Sources</h1>
          <p className="text-muted-foreground mt-1">Data source registry and last ingestion status</p>
        </div>
        <ExportButton />
      </div>

      {sources ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {sources.map((s) => (
            <Card key={s.source_id}>
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-sm font-semibold leading-tight">{s.source_name}</CardTitle>
                  <div className="flex items-center gap-1 shrink-0">
                    <Badge variant="outline" className="text-[10px]">{s.source_class}</Badge>
                    {s.is_enabled ? (
                      <Badge variant="success" className="text-[10px]">On</Badge>
                    ) : (
                      <Badge variant="secondary" className="text-[10px]">Off</Badge>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="text-xs space-y-1.5">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Province</span>
                  <span>{s.province ?? "—"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Type</span>
                  <span>{s.source_type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Schedule</span>
                  <code className="font-mono">{s.schedule_cron ?? "—"}</code>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Last run</span>
                  <span>
                    {s.last_run_at ? new Date(s.last_run_at).toLocaleDateString("en-CA") : "Never"}
                  </span>
                </div>
                {s.last_run_status && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Status</span>
                    <Badge
                      variant={
                        s.last_run_status === "COMPLETED" ? "success" :
                        s.last_run_status === "FAILED" ? "destructive" : "secondary"
                      }
                      className="text-[10px]"
                    >
                      {s.last_run_status}
                    </Badge>
                  </div>
                )}
                {s.last_run_record_count !== null && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Records</span>
                    <span className="tabular-nums">{s.last_run_record_count?.toLocaleString()}</span>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            Could not load sources. Ensure the API is running.
          </CardContent>
        </Card>
      )}
    </div>
  );
}
