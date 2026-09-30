import { BusinessHistoryResponse } from "@/lib/api";
import { Badge } from "@/components/ui/badge";

export function ProvenancePanel({ history }: { history: BusinessHistoryResponse }) {
  if (!history.fields || history.fields.length === 0) {
    return <p className="text-sm text-muted-foreground">No field history available.</p>;
  }

  return (
    <div className="space-y-6 text-sm">
      {history.fields.map(({ field_name, observations }) => (
        <div key={field_name}>
          <h4 className="font-medium capitalize mb-2">{field_name.replace(/_/g, " ")}</h4>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b text-muted-foreground">
                  <th className="text-left py-1 pr-3">Value</th>
                  <th className="text-left py-1 pr-3">Observed</th>
                  <th className="text-left py-1 pr-3">Confidence</th>
                  <th className="text-left py-1">Current</th>
                </tr>
              </thead>
              <tbody>
                {observations.map((obs) => (
                  <tr key={obs.observation_id} className="border-b last:border-0">
                    <td className="py-1 pr-3 max-w-[200px] truncate" title={obs.normalised_value ?? obs.raw_value ?? ""}>
                      {obs.normalised_value ?? obs.raw_value ?? "—"}
                    </td>
                    <td className="py-1 pr-3 text-muted-foreground">
                      {new Date(obs.observed_at).toLocaleDateString("en-CA")}
                    </td>
                    <td className="py-1 pr-3">
                      {obs.confidence ? (
                        <Badge variant="outline" className="text-[10px]">{obs.confidence}</Badge>
                      ) : "—"}
                    </td>
                    <td className="py-1">
                      {obs.is_current ? (
                        <Badge variant="success" className="text-[10px]">Current</Badge>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  );
}
