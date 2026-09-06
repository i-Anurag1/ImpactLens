import type { RiskLevel } from "../lib/api";

export default function RiskBadge({ level, score }: { level: RiskLevel; score?: number }) {
  return (
    <span className={`risk-${level} bg-risk-${level} border px-2.5 py-1 rounded-sm text-xs font-medium inline-flex items-center gap-1.5`}>
      {level}
      {typeof score === "number" && <span className="opacity-70">· {score}/100</span>}
    </span>
  );
}
