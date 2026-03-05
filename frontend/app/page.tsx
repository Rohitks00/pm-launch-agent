"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { apiFetch } from "@/lib/api";

interface Run { id: number; filename?: string; raw_input: string; status: string; created_at: string; }
const STATUS_VARIANT: Record<string, any> = { processing: "secondary", review: "outline", approved: "default", rejected: "destructive" };

export default function HomePage() {
  const router = useRouter();
  const [runs, setRuns] = useState<Run[]>([]);
  const [hasBrandKit, setHasBrandKit] = useState<boolean | null>(null);

  useEffect(() => {
    apiFetch("/api/brand-kit").then(() => setHasBrandKit(true)).catch(() => setHasBrandKit(false));
    apiFetch<Run[]>("/api/runs").then(setRuns).catch(() => {});
  }, []);

  if (hasBrandKit === false) return (
    <main className="container mx-auto px-4 py-24 text-center">
      <h1 className="text-3xl font-bold mb-4">Welcome to PM Launch Agent</h1>
      <p className="text-muted-foreground mb-8">Set up your brand kit before your first run.</p>
      <Button onClick={() => router.push("/setup")}>Set up brand kit</Button>
    </main>
  );

  return (
    <main className="container mx-auto px-4 py-12">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold">PM Launch Agent</h1>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => router.push("/setup")}>Brand Kit</Button>
          <Button onClick={() => router.push("/run")}>New Run</Button>
        </div>
      </div>
      {runs.length === 0 ? <p className="text-muted-foreground">No runs yet. Submit a PM document to start.</p> : (
        <div className="space-y-3">
          {runs.map(run => (
            <div key={run.id} className="border rounded-lg p-4 flex items-center justify-between cursor-pointer hover:bg-muted/50" onClick={() => router.push(`/review/${run.id}`)}>
              <div>
                <p className="font-medium">{run.filename || run.raw_input.slice(0, 60) + "..."}</p>
                <p className="text-sm text-muted-foreground">{new Date(run.created_at).toLocaleDateString()}</p>
              </div>
              <Badge variant={STATUS_VARIANT[run.status]}>{run.status}</Badge>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
