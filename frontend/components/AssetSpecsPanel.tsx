"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { apiFetch } from "@/lib/api";

interface Output { id: number; content: any; status: string; }

export function AssetSpecsPanel({ output }: { output: Output }) {
  const [status, setStatus] = useState(output.status);
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const assets = output.content?.assets ?? [];

  const approve = async () => {
    await apiFetch(`/api/outputs/${output.id}/approve`, { method: "POST", body: JSON.stringify({ status: "approved" }) });
    setStatus("approved");
  };

  const reject = async () => {
    setSubmitting(true);
    await apiFetch(`/api/outputs/${output.id}/approve`, { method: "POST", body: JSON.stringify({ status: "rejected", feedback }) });
    setStatus("draft"); setShowFeedback(false); setFeedback(""); setSubmitting(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Asset Specs</h2>
        <Badge variant={status === "approved" ? "default" : "secondary"}>{status}</Badge>
      </div>
      <div className="space-y-3">
        {assets.map((a: any, i: number) => (
          <div key={i} className="border rounded-lg p-4 space-y-1">
            <p className="font-medium">{a.name}</p>
            <p className="text-sm text-muted-foreground">{a.format} · {a.dimensions} · {a.placement}</p>
            <p className="text-sm">{a.notes}</p>
          </div>
        ))}
      </div>
      {status !== "approved" && (
        <div className="flex gap-2">
          <Button onClick={approve}>Approve All</Button>
          <Button variant="outline" onClick={() => setShowFeedback(!showFeedback)}>Request Changes</Button>
        </div>
      )}
      {showFeedback && (
        <div className="space-y-2">
          <Textarea value={feedback} onChange={e => setFeedback(e.target.value)} placeholder="Describe what needs to change..." rows={3} />
          <Button size="sm" onClick={reject} disabled={submitting || !feedback.trim()}>Submit & Regenerate</Button>
        </div>
      )}
    </div>
  );
}
