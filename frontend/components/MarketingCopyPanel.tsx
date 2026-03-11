"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { apiFetch } from "@/lib/api";

interface Output { id: number; content: any; status: string; }

export function MarketingCopyPanel({ output }: { output: Output }) {
  const [status, setStatus] = useState(output.status);
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const c = output.content;

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
        <h2 className="text-xl font-semibold">Marketing Copy</h2>
        <Badge variant={status === "approved" ? "default" : "secondary"}>{status}</Badge>
      </div>
      <section className="space-y-2">
        <h3 className="font-medium text-sm uppercase text-muted-foreground">Email</h3>
        <div className="border rounded-lg p-4 space-y-2">
          <p><span className="font-medium">Subject:</span> {c.email?.subject}</p>
          <p className="text-sm whitespace-pre-wrap">{c.email?.body}</p>
          {c.email?.alt_subjects?.map((s: string, i: number) => <p key={i} className="text-sm text-muted-foreground">{s}</p>)}
        </div>
      </section>
      <section className="space-y-2">
        <h3 className="font-medium text-sm uppercase text-muted-foreground">Landing Page</h3>
        <div className="border rounded-lg p-4 space-y-1">
          <p><span className="font-medium">Headline:</span> {c.landing_page?.headline}</p>
          <p><span className="font-medium">Subheadline:</span> {c.landing_page?.subheadline}</p>
          <p><span className="font-medium">CTA:</span> {c.landing_page?.cta}</p>
        </div>
      </section>
      <section className="space-y-2">
        <h3 className="font-medium text-sm uppercase text-muted-foreground">Social</h3>
        {c.social?.map((s: any, i: number) => (
          <div key={i} className="border rounded-lg p-4">
            <p className="text-xs font-medium text-muted-foreground">{s.platform}</p>
            <p className="text-sm mt-1">{s.copy}</p>
          </div>
        ))}
      </section>
      {c.press_release && (
        <section className="space-y-2">
          <h3 className="font-medium text-sm uppercase text-muted-foreground">Press Release</h3>
          <div className="border rounded-lg p-4 space-y-2">
            <p className="font-medium">{c.press_release.headline}</p>
            <p className="text-sm whitespace-pre-wrap">{c.press_release.body}</p>
            {c.press_release.boilerplate && (
              <p className="text-xs text-muted-foreground border-t pt-2 mt-2">{c.press_release.boilerplate}</p>
            )}
          </div>
        </section>
      )}
      {c.fact_sheet && (
        <section className="space-y-2">
          <h3 className="font-medium text-sm uppercase text-muted-foreground">Fact Sheet</h3>
          <div className="border rounded-lg p-4 space-y-2">
            <p><span className="font-medium">Company:</span> {c.fact_sheet.company}</p>
            <p><span className="font-medium">Product:</span> {c.fact_sheet.product}</p>
            {c.fact_sheet.key_facts?.length > 0 && (
              <ul className="text-sm list-disc list-inside space-y-1">
                {c.fact_sheet.key_facts.map((f: string, i: number) => <li key={i}>{f}</li>)}
              </ul>
            )}
            {c.fact_sheet.contact && (
              <p className="text-sm text-muted-foreground">Contact: {c.fact_sheet.contact}</p>
            )}
          </div>
        </section>
      )}
      {status !== "approved" && (
        <div className="flex gap-2">
          <Button onClick={approve}>Approve</Button>
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
