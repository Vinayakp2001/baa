"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

export function DncFlagButton({ entityId }: { entityId: string }) {
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleDnc() {
    if (!confirm("Mark this business as Do Not Contact (DNC)?")) return;
    setLoading(true);
    try {
      await api.businesses.setFlag(entityId, "DNC");
      router.refresh();
    } catch (e) {
      alert("Failed to set DNC flag.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Button variant="outline" size="sm" onClick={handleDnc} disabled={loading} className="shrink-0">
      {loading ? "Saving…" : "Mark DNC"}
    </Button>
  );
}
