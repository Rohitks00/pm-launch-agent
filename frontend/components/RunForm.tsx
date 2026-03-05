"use client";
import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { apiFetch } from "@/lib/api";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Props { brandKitId: number; onRunCreated: (id: number) => void; }

export function RunForm({ brandKitId, onRunCreated }: Props) {
  const [pasteText, setPasteText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const submitPaste = async () => {
    setSubmitting(true); setError("");
    try {
      const run = await apiFetch<{ id: number }>("/api/runs", { method: "POST", body: JSON.stringify({ brand_kit_id: brandKitId, raw_input: pasteText }) });
      onRunCreated(run.id);
    } catch (err: any) { setError(err.message); setSubmitting(false); }
  };

  const submitFile = async () => {
    if (!file) return;
    setSubmitting(true); setError("");
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("brand_kit_id", String(brandKitId));
      const res = await fetch(`${API}/api/runs/upload`, { method: "POST", body: fd });
      if (!res.ok) throw new Error("Upload failed");
      const run = await res.json();
      onRunCreated(run.id);
    } catch (err: any) { setError(err.message); setSubmitting(false); }
  };

  return (
    <Tabs defaultValue="paste">
      <TabsList><TabsTrigger value="paste">Paste Text</TabsTrigger><TabsTrigger value="upload">Upload File</TabsTrigger></TabsList>
      <TabsContent value="paste" className="space-y-4">
        <p className="text-sm text-muted-foreground">Paste your PM launch notes, PRD, or any product document.</p>
        <Textarea value={pasteText} onChange={e => setPasteText(e.target.value)} rows={16} placeholder="# Feature Launch&#10;&#10;Paste your PM document here..." />
        {error && <p className="text-red-500 text-sm">{error}</p>}
        <Button onClick={submitPaste} disabled={submitting || !pasteText.trim()}>{submitting ? "Submitting..." : "Generate Assets"}</Button>
      </TabsContent>
      <TabsContent value="upload" className="space-y-4">
        <p className="text-sm text-muted-foreground">Upload a PDF, Word doc (.docx), or Markdown file.</p>
        <div className="border-2 border-dashed rounded-lg p-12 text-center cursor-pointer hover:bg-muted/50" onClick={() => fileRef.current?.click()}>
          {file ? <p className="font-medium">{file.name}</p> : <p className="text-muted-foreground">Drop a file or click to browse</p>}
          <input ref={fileRef} type="file" accept=".pdf,.docx,.md,.txt" className="hidden" onChange={e => setFile(e.target.files?.[0] ?? null)} />
        </div>
        {error && <p className="text-red-500 text-sm">{error}</p>}
        <Button onClick={submitFile} disabled={submitting || !file}>{submitting ? "Uploading..." : "Generate Assets"}</Button>
      </TabsContent>
    </Tabs>
  );
}
