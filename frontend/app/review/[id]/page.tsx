"use client";
import { use, useEffect, useState } from "react";
import { ProgressScreen } from "@/components/ProgressScreen";
import { MarketingCopyPanel } from "@/components/MarketingCopyPanel";
import { AssetSpecsPanel } from "@/components/AssetSpecsPanel";
import { apiFetch } from "@/lib/api";

interface Output { id: number; output_type: string; content: any; status: string; }

export default function ReviewPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const runId = parseInt(id);
  const [ready, setReady] = useState(false);
  const [outputs, setOutputs] = useState<Output[]>([]);

  const loadOutputs = async () => {
    const data = await apiFetch<Output[]>(`/api/runs/${runId}/outputs`);
    setOutputs(data);
    setReady(true);
  };

  useEffect(() => {
    apiFetch<{ status: string }>(`/api/runs/${runId}`).then(run => {
      if (run.status === "review" || run.status === "approved") loadOutputs();
    });
  }, []);

  const copyOutput = outputs.find(o => o.output_type === "marketing_copy");
  const briefOutput = outputs.find(o => o.output_type === "asset_specs");

  return (
    <main className="container mx-auto px-4 py-12">
      {!ready ? (
        <ProgressScreen runId={runId} onReady={loadOutputs} />
      ) : (
        <div>
          <h1 className="text-3xl font-bold mb-8">Review Assets</h1>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {copyOutput && <MarketingCopyPanel output={copyOutput} />}
            {briefOutput && <AssetSpecsPanel output={briefOutput} />}
          </div>
        </div>
      )}
    </main>
  );
}
