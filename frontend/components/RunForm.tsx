"use client";
import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/api";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const CHECKLIST = [
  {
    category: "PR Releases",
    items: [
      { key: "press_release", label: "Press release draft", defaultChecked: false },
      { key: "fact_sheet", label: "Fact sheet / media brief", defaultChecked: false },
      { key: "media_kit_specs", label: "Media kit asset specs", defaultChecked: false },
    ],
  },
  {
    category: "Marketing Copy",
    items: [
      { key: "email", label: "Email copy (subject + body)", defaultChecked: true },
      { key: "landing_page", label: "Landing page copy", defaultChecked: true },
      { key: "social", label: "Social posts (LinkedIn, Twitter/X)", defaultChecked: true },
    ],
  },
  {
    category: "Design Assets",
    items: [
      { key: "hero_image", label: "Hero image spec", defaultChecked: true },
      { key: "social_graphics", label: "Social media graphics spec", defaultChecked: true },
      { key: "email_header", label: "Email header graphic spec", defaultChecked: false },
      { key: "feature_illustrations", label: "Feature illustrations spec", defaultChecked: false },
    ],
  },
];

const DEFAULT_ENABLED = CHECKLIST.flatMap(c => c.items.filter(i => i.defaultChecked).map(i => i.key));

interface Props { brandKitId: number; onRunCreated: (id: number) => void; }

export function RunForm({ brandKitId, onRunCreated }: Props) {
  const [pasteText, setPasteText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [enabledOutputs, setEnabledOutputs] = useState<string[]>(DEFAULT_ENABLED);
  const fileRef = useRef<HTMLInputElement>(null);

  const toggleOutput = (key: string) => {
    setEnabledOutputs(prev =>
      prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key]
    );
  };

  const submitPaste = async () => {
    setSubmitting(true); setError("");
    try {
      const run = await apiFetch<{ id: number }>("/api/runs", {
        method: "POST",
        body: JSON.stringify({ brand_kit_id: brandKitId, raw_input: pasteText, enabled_outputs: enabledOutputs }),
      });
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
      fd.append("enabled_outputs", JSON.stringify(enabledOutputs));
      const res = await fetch(`${API}/api/runs/upload`, { method: "POST", body: fd });
      if (!res.ok) throw new Error("Upload failed");
      const run = await res.json();
      onRunCreated(run.id);
    } catch (err: any) { setError(err.message); setSubmitting(false); }
  };

  return (
    <div className="space-y-8">
      <Tabs defaultValue="paste">
        <TabsList>
          <TabsTrigger value="paste">Paste Text</TabsTrigger>
          <TabsTrigger value="upload">Upload File</TabsTrigger>
        </TabsList>
        <TabsContent value="paste" className="space-y-4">
          <p className="text-sm text-muted-foreground">Paste your PM launch notes, PRD, or any product document.</p>
          <Textarea
            value={pasteText}
            onChange={e => setPasteText(e.target.value)}
            rows={16}
            placeholder={"# Feature Launch\n\nPaste your PM document here..."}
          />
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <Button onClick={submitPaste} disabled={submitting || !pasteText.trim() || enabledOutputs.length === 0}>
            {submitting ? "Submitting..." : "Generate Assets"}
          </Button>
        </TabsContent>
        <TabsContent value="upload" className="space-y-4">
          <p className="text-sm text-muted-foreground">Upload a PDF, Word doc (.docx), or Markdown file.</p>
          <div
            className="border-2 border-dashed rounded-lg p-12 text-center cursor-pointer hover:bg-muted/50"
            onClick={() => fileRef.current?.click()}
          >
            {file
              ? <p className="font-medium">{file.name}</p>
              : <p className="text-muted-foreground">Drop a file or click to browse</p>
            }
            <input
              ref={fileRef}
              type="file"
              accept=".pdf,.docx,.md,.txt"
              className="hidden"
              onChange={e => setFile(e.target.files?.[0] ?? null)}
            />
          </div>
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <Button onClick={submitFile} disabled={submitting || !file || enabledOutputs.length === 0}>
            {submitting ? "Uploading..." : "Generate Assets"}
          </Button>
        </TabsContent>
      </Tabs>

      {/* Asset Checklist */}
      <div className="space-y-4 border-t pt-6">
        <div>
          <h2 className="text-base font-semibold">Select assets to generate</h2>
          <p className="text-sm text-muted-foreground">Only checked items will be generated by the AI pipeline.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {CHECKLIST.map(group => (
            <div key={group.category} className="space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                {group.category}
              </h3>
              {group.items.map(item => (
                <div key={item.key} className="flex items-center gap-2">
                  <Checkbox
                    id={item.key}
                    checked={enabledOutputs.includes(item.key)}
                    onCheckedChange={() => toggleOutput(item.key)}
                  />
                  <Label htmlFor={item.key} className="text-sm font-normal cursor-pointer">
                    {item.label}
                  </Label>
                </div>
              ))}
            </div>
          ))}
        </div>
        {enabledOutputs.length === 0 && (
          <p className="text-sm text-red-500">Select at least one asset to generate.</p>
        )}
      </div>
    </div>
  );
}
