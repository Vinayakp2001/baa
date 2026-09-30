"use client";

import { useRouter, usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";

const PROVINCES = ["AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "QC", "SK", "YT"];
const STATUSES = ["ACTIVE", "INACTIVE", "SUSPENDED", "DISSOLVED", "PENDING", "UNKNOWN"];
const EMPLOYEE_BUCKETS = ["1-4", "5-9", "10-19", "20-49", "50-99", "100-199", "200-499", "500+"];
const NAICS_SECTORS = [
  "11", "21", "22", "23", "31", "32", "33", "41", "44", "45",
  "48", "49", "51", "52", "53", "54", "55", "56", "61", "62",
  "71", "72", "81", "91",
];

interface Props {
  current: Record<string, string | undefined>;
}

export function FilterPanel({ current }: Props) {
  const router = useRouter();
  const pathname = usePathname();

  function apply(updates: Record<string, string | undefined>) {
    const params = new URLSearchParams();
    const merged = { ...current, ...updates, page: "1" };
    Object.entries(merged).forEach(([k, v]) => {
      if (v !== undefined && v !== "" && v !== "false") params.set(k, v);
    });
    router.push(`${pathname}?${params.toString()}`);
  }

  function clear() {
    router.push(pathname);
  }

  const sel = (field: string) => current[field] ?? "";

  return (
    <div className="space-y-5 text-sm">
      <div className="flex items-center justify-between">
        <span className="font-semibold">Filters</span>
        <Button variant="ghost" size="sm" onClick={clear}>Clear all</Button>
      </div>

      <FilterGroup label="Province">
        <select
          className="w-full rounded border border-input bg-background px-2 py-1.5 text-sm"
          value={sel("province")}
          onChange={(e) => apply({ province: e.target.value || undefined })}
        >
          <option value="">All</option>
          {PROVINCES.map((p) => <option key={p} value={p}>{p}</option>)}
        </select>
      </FilterGroup>

      <FilterGroup label="Status">
        <select
          className="w-full rounded border border-input bg-background px-2 py-1.5 text-sm"
          value={sel("status")}
          onChange={(e) => apply({ status: e.target.value || undefined })}
        >
          <option value="">All</option>
          {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </FilterGroup>

      <FilterGroup label="Employee Bucket">
        <select
          className="w-full rounded border border-input bg-background px-2 py-1.5 text-sm"
          value={sel("employee_bucket")}
          onChange={(e) => apply({ employee_bucket: e.target.value || undefined })}
        >
          <option value="">All</option>
          {EMPLOYEE_BUCKETS.map((b) => <option key={b} value={b}>{b}</option>)}
        </select>
      </FilterGroup>

      <FilterGroup label="NAICS Sector">
        <select
          className="w-full rounded border border-input bg-background px-2 py-1.5 text-sm"
          value={sel("naics_sector")}
          onChange={(e) => apply({ naics_sector: e.target.value || undefined })}
        >
          <option value="">All</option>
          {NAICS_SECTORS.map((n) => <option key={n} value={n}>{n}</option>)}
        </select>
      </FilterGroup>

      <FilterGroup label="City">
        <input
          type="text"
          placeholder="e.g. Calgary"
          className="w-full rounded border border-input bg-background px-2 py-1.5 text-sm"
          defaultValue={sel("city")}
          onBlur={(e) => apply({ city: e.target.value || undefined })}
          onKeyDown={(e) => {
            if (e.key === "Enter") apply({ city: (e.target as HTMLInputElement).value || undefined });
          }}
        />
      </FilterGroup>

      <FilterGroup label="New since (date)">
        <input
          type="date"
          className="w-full rounded border border-input bg-background px-2 py-1.5 text-sm"
          defaultValue={sel("new_since")}
          onChange={(e) => apply({ new_since: e.target.value || undefined })}
        />
      </FilterGroup>

      <div className="space-y-2">
        <span className="font-medium text-muted-foreground">Contact / Data</span>
        {[
          ["sales_ready", "Sales ready only"],
          ["has_phone", "Has phone"],
          ["has_email", "Has email"],
          ["has_website", "Has website"],
          ["has_director", "Has director"],
        ].map(([key, label]) => (
          <label key={key} className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={current[key] === "true"}
              onChange={(e) => apply({ [key]: e.target.checked ? "true" : undefined })}
              className="rounded border-input"
            />
            <span>{label}</span>
          </label>
        ))}
      </div>

      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={current.dnc === "true"}
          onChange={(e) => apply({ dnc: e.target.checked ? "true" : undefined })}
          className="rounded border-input"
        />
        <span className="text-destructive font-medium">Include DNC</span>
      </label>
    </div>
  );
}

function FilterGroup({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <label className="font-medium text-muted-foreground">{label}</label>
      {children}
    </div>
  );
}
