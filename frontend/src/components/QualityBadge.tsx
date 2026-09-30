import { cn } from "@/lib/utils";

export function QualityBadge({ score }: { score: number | null }) {
  if (score === null) return <span className="text-muted-foreground text-xs">—</span>;

  const color =
    score >= 70 ? "bg-green-100 text-green-800" :
    score >= 40 ? "bg-yellow-100 text-yellow-800" :
    "bg-red-100 text-red-800";

  return (
    <span className={cn("inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold tabular-nums", color)}>
      {score}
    </span>
  );
}
