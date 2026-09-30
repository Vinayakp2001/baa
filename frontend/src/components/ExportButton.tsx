"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";

export function ExportButton({
  filters = {},
}: {
  filters?: Record<string, string | boolean | undefined>;
}) {
  const [includeDnc, setIncludeDnc] = useState(false);
  const [format, setFormat] = useState<"csv" | "json">("csv");

  function handleExport() {
    const url = api.export.url({
      ...filters,
      format,
      include_dnc: includeDnc ? "true" : undefined,
    });
    window.open(url, "_blank");
  }

  return (
    <div className="flex items-center gap-3">
      <label className="flex items-center gap-1.5 text-sm cursor-pointer">
        <input
          type="checkbox"
          checked={includeDnc}
          onChange={(e) => setIncludeDnc(e.target.checked)}
          className="rounded border-input"
        />
        <span className="text-destructive font-medium">Include DNC</span>
      </label>
      <select
        value={format}
        onChange={(e) => setFormat(e.target.value as "csv" | "json")}
        className="rounded border border-input bg-background px-2 py-1.5 text-sm"
      >
        <option value="csv">CSV</option>
        <option value="json">JSON</option>
      </select>
      <Button onClick={handleExport} size="sm">
        Export
      </Button>
    </div>
  );
}
