import { LivePredictionShell } from "@/components/live-prediction-shell";

export default function HomePage() {
  return (
    <main className="min-h-screen px-4 py-6 md:px-8">
      <div className="mx-auto flex max-w-7xl flex-col gap-6">
        <LivePredictionShell />
      </div>
    </main>
  );
}
