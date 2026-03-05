"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { RunForm } from "@/components/RunForm";
import { apiFetch } from "@/lib/api";

export default function RunPage() {
  const router = useRouter();
  const [brandKitId, setBrandKitId] = useState<number | null>(null);
  useEffect(() => {
    apiFetch<{ id: number }>("/api/brand-kit").then(k => setBrandKitId(k.id)).catch(() => router.push("/setup"));
  }, []);
  if (!brandKitId) return <div className="container mx-auto px-4 py-12">Loading...</div>;
  return (
    <main className="container mx-auto px-4 py-12 max-w-3xl">
      <h1 className="text-3xl font-bold mb-2">New Run</h1>
      <p className="text-muted-foreground mb-8">Submit a PM document to generate marketing copy and asset specs.</p>
      <RunForm brandKitId={brandKitId} onRunCreated={id => router.push(`/review/${id}`)} />
    </main>
  );
}
