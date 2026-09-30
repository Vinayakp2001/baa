import { Suspense } from "react";
import { api } from "@/lib/api";
import { BusinessTable } from "@/components/BusinessTable";
import { FilterPanel } from "@/components/FilterPanel";

export const dynamic = "force-dynamic";

interface PageProps {
  searchParams: Record<string, string | undefined>;
}

export default async function BusinessesPage({ searchParams }: PageProps) {
  const filters = {
    province: searchParams.province,
    city: searchParams.city,
    naics_sector: searchParams.naics_sector,
    employee_bucket: searchParams.employee_bucket,
    status: searchParams.status,
    sales_ready: searchParams.sales_ready === "true" ? true : undefined,
    has_phone: searchParams.has_phone === "true" ? true : undefined,
    has_email: searchParams.has_email === "true" ? true : undefined,
    has_website: searchParams.has_website === "true" ? true : undefined,
    has_director: searchParams.has_director === "true" ? true : undefined,
    new_since: searchParams.new_since,
    event_type: searchParams.event_type,
    dnc: searchParams.dnc === "true" ? true : undefined,
    page: searchParams.page ? parseInt(searchParams.page) : 1,
    page_size: 50,
  };

  let data;
  try {
    data = await api.businesses.list(filters);
  } catch {
    data = null;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Businesses</h1>
        <p className="text-muted-foreground mt-1">
          {data ? `${data.total.toLocaleString()} total` : "Browse and filter the business registry"}
        </p>
      </div>

      <div className="flex gap-6">
        <aside className="w-64 shrink-0">
          <FilterPanel current={searchParams} />
        </aside>
        <div className="flex-1 min-w-0">
          <Suspense fallback={<div className="text-muted-foreground text-sm">Loading…</div>}>
            {data ? (
              <BusinessTable data={data} currentPage={filters.page ?? 1} searchParams={searchParams} />
            ) : (
              <div className="rounded-lg border p-8 text-center text-muted-foreground">
                Could not load businesses. Ensure the API is running.
              </div>
            )}
          </Suspense>
        </div>
      </div>
    </div>
  );
}
