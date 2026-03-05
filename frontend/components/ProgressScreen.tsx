"use client";
import { useEffect, useState } from "react";
import { Progress } from "@/components/ui/progress";
import { apiFetch } from "@/lib/api";

const STEPS = [
  { key: "orchestrator", label: "Reading document" },
  { key: "copy_agent", label: "Generating copy" },
  { key: "brief_agent", label: "Generating asset specs" },
];

export function ProgressScreen({ runId, onReady }: { runId: number; onReady: () => void }) {
  const [progress, setProgress] = useState<Record<string, string>>({});
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    const poll = setInterval(async () => {
      const run = await apiFetch<{ status: string; progress: Record<string, string> }>(`/api/runs/${runId}`);
      setProgress(run.progress);
      if (run.status === "review" || run.status === "approved") { clearInterval(poll); onReady(); }
      if (run.status === "rejected") { clearInterval(poll); setFailed(true); }
    }, 2000);
    return () => clearInterval(poll);
  }, [runId]);

  const doneCount = STEPS.filter(s => progress[s.key] === "done").length;

  return (
    <div className="space-y-8 max-w-md mx-auto text-center py-24">
      <h2 className="text-2xl font-semibold">Generating your assets...</h2>
      <Progress value={(doneCount / STEPS.length) * 100} />
      <div className="space-y-3 text-left">
        {STEPS.map(s => {
          const state = progress[s.key] ?? "pending";
          return (
            <div key={s.key} className="flex items-center gap-3">
              <span>{state === "done" ? "✓" : state === "running" ? "⏳" : "○"}</span>
              <span className={state === "done" ? "text-green-600" : state === "running" ? "text-blue-600" : "text-muted-foreground"}>{s.label}</span>
            </div>
          );
        })}
      </div>
      {failed && <p className="text-red-500">Pipeline failed. Please try submitting again.</p>}
    </div>
  );
}
