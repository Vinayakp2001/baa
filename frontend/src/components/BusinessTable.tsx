import Link from "next/link";
import { PaginatedBusinesses } from "@/lib/api";
import { QualityBadge } from "@/components/QualityBadge";
import { Badge } from "@/components/ui/badge";

interface Props {
  data: PaginatedBusinesses;
  currentPage: number;
  searchParams: Record<string, string | undefined>;
}

const statusVariant = (s: string | null) => {
  if (!s) return "secondary";
  if (s === "ACTIVE") return "success";
  if (s === "INACTIVE" || s === "DISSOLVED") return "destructive";
  return "secondary";
};

export function BusinessTable({ data, currentPage, searchParams }: Props) {
  const buildPageUrl = (page: number) => {
    const params = new URLSearchParams();
    Object.entries({ ...searchParams, page: String(page) }).forEach(([k, v]) => {
      if (v) params.set(k, v);
    });
    return `/businesses?${params.toString()}`;
  };

  const totalPages = Math.ceil(data.total / data.page_size);

  return (
    <div className="space-y-4">
      <div className="overflow-x-auto rounded-lg border">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">Business</th>
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">Province</th>
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">Status</th>
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">Score</th>
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">First Seen</th>
            </tr>
          </thead>
          <tbody>
            {data.results.map((b) => (
              <tr key={b.entity_id} className="border-t hover:bg-muted/30 transition-colors">
                <td className="px-4 py-3">
                  <Link
                    href={`/businesses/${b.entity_id}`}
                    className="font-medium text-primary hover:underline"
                  >
                    {b.canonical_name}
                  </Link>
                  {b.trade_name && b.trade_name !== b.canonical_name && (
                    <p className="text-xs text-muted-foreground">{b.trade_name}</p>
                  )}
                  {b.sales_ready && (
                    <Badge variant="success" className="mt-1 text-[10px]">Sales Ready</Badge>
                  )}
                </td>
                <td className="px-4 py-3 text-muted-foreground">{b.province ?? "—"}</td>
                <td className="px-4 py-3">
                  <Badge variant={statusVariant(b.status) as "success" | "destructive" | "secondary"}>
                    {b.status ?? "UNKNOWN"}
                  </Badge>
                </td>
                <td className="px-4 py-3">
                  <QualityBadge score={b.lead_quality_score} />
                </td>
                <td className="px-4 py-3 text-muted-foreground text-xs">
                  {b.first_seen_at ? new Date(b.first_seen_at).toLocaleDateString("en-CA") : "—"}
                </td>
              </tr>
            ))}
            {data.results.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-12 text-center text-muted-foreground">
                  No businesses match the current filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">
            Page {currentPage} of {totalPages} ({data.total.toLocaleString()} results)
          </span>
          <div className="flex gap-2">
            {currentPage > 1 && (
              <Link
                href={buildPageUrl(currentPage - 1)}
                className="rounded border px-3 py-1 hover:bg-muted transition-colors"
              >
                Previous
              </Link>
            )}
            {currentPage < totalPages && (
              <Link
                href={buildPageUrl(currentPage + 1)}
                className="rounded border px-3 py-1 hover:bg-muted transition-colors"
              >
                Next
              </Link>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
