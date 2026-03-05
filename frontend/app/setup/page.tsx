"use client";
import { useRouter } from "next/navigation";
import { BrandKitForm } from "@/components/BrandKitForm";

export default function SetupPage() {
  const router = useRouter();
  return (
    <main className="container mx-auto px-4 py-12">
      <h1 className="text-3xl font-bold mb-2">Brand Kit Setup</h1>
      <p className="text-muted-foreground mb-8">Configure your brand once. Used for all future runs.</p>
      <BrandKitForm onSave={() => router.push("/")} />
    </main>
  );
}
