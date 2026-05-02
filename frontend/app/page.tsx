import { ChallengerList, WinnerCard } from "@/components/prediction-card";
import { getNextRacePrediction } from "@/lib/api/client";

export default async function HomePage() {
  const prediction = await getNextRacePrediction();

  return (
    <main className="min-h-screen px-4 py-6 md:px-8">
      <div className="mx-auto flex max-w-7xl flex-col gap-6">
        <header className="glass rounded-[32px] p-8 shadow-2xl shadow-black/30">
          <div className="text-xs uppercase tracking-[0.32em] text-red-300">F1 Prediction Engine</div>
          {prediction ? (
            <div className="mt-4 inline-flex rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-xs uppercase tracking-[0.24em] text-zinc-300">
              Predicting: {prediction.target.eventName} · Round {prediction.target.round}
            </div>
          ) : null}
          <h1 className="mt-3 max-w-4xl text-4xl font-semibold tracking-tight md:text-6xl">
            Predict who wins the next Grand Prix before lights out.
          </h1>
          <p className="mt-4 max-w-3xl text-sm leading-6 text-zinc-400 md:text-base">
            {prediction
              ? `The model blends recent form, historical track performance, teammate-relative strength, DNF risk, and live weather context to rank the field for ${prediction.target.eventName}.`
              : "The hosted app only shows a winner when the live prediction API returns a real model result. No placeholder winner is shown."}
          </p>
        </header>

        {prediction ? (
          <>
            <section className="grid gap-6 xl:grid-cols-[1.2fr_0.9fr]">
              <WinnerCard
                driver={prediction.winner}
                eventName={prediction.target.eventName}
                round={prediction.target.round}
              />
              <section className="glass rounded-[28px] p-6 shadow-2xl shadow-black/30">
                <div className="text-xs uppercase tracking-[0.24em] text-zinc-500">Grand Prix Being Predicted</div>
                <h2 className="mt-3 text-3xl font-semibold">{prediction.target.eventName}</h2>
                <p className="mt-2 text-sm text-zinc-400">
                  Round {prediction.target.round} · {prediction.target.circuitName} · {prediction.target.country} · {prediction.target.eventDate}
                </p>

                <div className="mt-6 grid gap-3">
                  <div className="rounded-2xl bg-white/[0.03] p-4">
                    <div className="text-xs uppercase tracking-[0.2em] text-zinc-500">Weather Outlook</div>
                    <div className="mt-2 text-xl font-semibold">{prediction.weather.conditionLabel}</div>
                    <div className="mt-1 text-sm text-zinc-400">
                      {prediction.weather.airTempC != null ? `${prediction.weather.airTempC.toFixed(1)}°C` : "n/a"} ·{" "}
                      {prediction.weather.rainProbability != null ? `${prediction.weather.rainProbability.toFixed(0)}% rain` : "rain n/a"}
                    </div>
                  </div>
                  <div className="rounded-2xl bg-white/[0.03] p-4">
                    <div className="text-xs uppercase tracking-[0.2em] text-zinc-500">Confidence Band</div>
                    <div className="mt-2 text-xl font-semibold">{prediction.confidenceBand.label}</div>
                    <div className="mt-1 text-sm text-zinc-400">
                      Winner gap to second: {(prediction.confidenceBand.winnerVsSecond * 100).toFixed(1)} points
                    </div>
                  </div>
                  <div className="rounded-2xl bg-white/[0.03] p-4">
                    <div className="text-xs uppercase tracking-[0.2em] text-zinc-500">Model</div>
                    <div className="mt-2 text-xl font-semibold">{prediction.model.name}</div>
                    <div className="mt-1 text-sm text-zinc-400">
                      {prediction.model.trainedSamples} samples · {prediction.model.featureCount} features
                    </div>
                  </div>
                </div>
              </section>
            </section>

            <section className="glass rounded-[28px] p-6 shadow-2xl shadow-black/30">
              <div className="mb-5 flex items-end justify-between gap-4">
                <div>
                  <div className="text-xs uppercase tracking-[0.24em] text-zinc-500">Nearest Results</div>
                  <h2 className="mt-2 text-3xl font-semibold">Closest challengers</h2>
                </div>
                <div className="text-sm text-zinc-500">Top alternatives if the favorite misses</div>
              </div>
              <ChallengerList drivers={prediction.challengers} />
            </section>
          </>
        ) : (
          <section className="glass rounded-[28px] p-8 shadow-2xl shadow-black/30">
            <div className="text-xs uppercase tracking-[0.28em] text-amber-300">Live Prediction Unavailable</div>
            <h2 className="mt-3 text-3xl font-semibold">No fallback winner is shown.</h2>
            <p className="mt-4 max-w-3xl text-sm leading-6 text-zinc-400 md:text-base">
              The hosted backend timed out before returning a real model result, so this page intentionally avoids
              showing a placeholder prediction. The localhost app is still using the real live model path.
            </p>
          </section>
        )}
      </div>
    </main>
  );
}
