"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/api";

interface Props { initial?: Record<string, any>; onSave: () => void; }

export function BrandKitForm({ initial, onSave }: Props) {
  const [form, setForm] = useState({
    name: initial?.name ?? "",
    voice_tone: initial?.voice_tone ?? "",
    do_list: (initial?.do_list ?? []).join("\n"),
    dont_list: (initial?.dont_list ?? []).join("\n"),
    style_rules: initial?.style_rules ?? "",
    colors: JSON.stringify(initial?.colors ?? { primary: "", accent: "" }, null, 2),
    typography: JSON.stringify(initial?.typography ?? { heading: "", body: "" }, null, 2),
    logo_url: initial?.logo_url ?? "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const set = (key: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm(f => ({ ...f, [key]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true); setError("");
    try {
      await apiFetch("/api/brand-kit", {
        method: initial ? "PUT" : "POST",
        body: JSON.stringify({
          ...form,
          do_list: form.do_list.split("\n").filter(Boolean),
          dont_list: form.dont_list.split("\n").filter(Boolean),
          colors: JSON.parse(form.colors),
          typography: JSON.parse(form.typography),
        }),
      });
      onSave();
    } catch (err: any) { setError(err.message); }
    finally { setSaving(false); }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-2xl">
      <div className="space-y-2"><Label>Brand Name</Label><Input value={form.name} onChange={set("name")} required /></div>
      <div className="space-y-2"><Label>Voice & Tone</Label><Textarea value={form.voice_tone} onChange={set("voice_tone")} rows={3} placeholder="Confident but approachable." /></div>
      <div className="space-y-2"><Label>DO List (one per line)</Label><Textarea value={form.do_list} onChange={set("do_list")} rows={4} placeholder="Lead with benefits&#10;Use active voice" /></div>
      <div className="space-y-2"><Label>DON&apos;T List (one per line)</Label><Textarea value={form.dont_list} onChange={set("dont_list")} rows={4} placeholder="No jargon&#10;No passive voice" /></div>
      <div className="space-y-2"><Label>Style Rules</Label><Textarea value={form.style_rules} onChange={set("style_rules")} rows={3} /></div>
      <div className="space-y-2"><Label>Colors (JSON)</Label><Textarea value={form.colors} onChange={set("colors")} rows={4} className="font-mono text-sm" /></div>
      <div className="space-y-2"><Label>Typography (JSON)</Label><Textarea value={form.typography} onChange={set("typography")} rows={4} className="font-mono text-sm" /></div>
      <div className="space-y-2"><Label>Logo URL</Label><Input value={form.logo_url} onChange={set("logo_url")} placeholder="/assets/logo.png" /></div>
      {error && <p className="text-red-500 text-sm">{error}</p>}
      <Button type="submit" disabled={saving}>{saving ? "Saving..." : "Save Brand Kit"}</Button>
    </form>
  );
}
