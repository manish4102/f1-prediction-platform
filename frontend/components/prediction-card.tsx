"use client";

import { motion } from "motion/react";

import type { DriverPrediction } from "@/lib/api/types";

function pct(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

export function WinnerCard({
  driver,
  eventName,
  round,
}: {
  driver: DriverPrediction;
  eventName: string;
  round: number;
}) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      className="glass rounded-[28px] p-6 shadow-2xl shadow-black/30"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-xs uppercase tracking-[0.32em] text-red-300">Projected Winner</div>
        <div className="rounded-full border border-red-500/25 bg-red-500/10 px-3 py-1 text-[11px] uppercase tracking-[0.24em] text-red-200">
          Round {round} · {eventName}
        </div>
      </div>
      <h2 className="mt-3 text-4xl font-semibold tracking-tight">{driver.fullName}</h2>
      <p className="mt-2 text-sm text-zinc-400">{driver.teamName}</p>
      <div className="mt-6 flex items-end justify-between gap-4">
        <div>
          <div className="text-xs uppercase tracking-[0.2em] text-zinc-500">Win Probability</div>
          <div className="mt-2 text-5xl font-semibold">{pct(driver.winProbability)}</div>
        </div>
        <div className="rounded-2xl bg-red-500/12 px-4 py-3 text-right">
          <div className="text-xs uppercase tracking-[0.2em] text-red-300">Score</div>
          <div className="mt-1 text-xl font-semibold text-white">{driver.score.toFixed(2)}</div>
        </div>
      </div>
      <div className="mt-6 space-y-2">
        {driver.explanation.map((line) => (
          <div key={line} className="rounded-2xl bg-white/[0.03] px-4 py-3 text-sm text-zinc-300">
            {line}
          </div>
        ))}
      </div>
    </motion.section>
  );
}

export function ChallengerList({ drivers }: { drivers: DriverPrediction[] }) {
  return (
    <div className="space-y-3">
      {drivers.map((driver, index) => (
        <motion.div
          key={driver.driverCode}
          initial={{ opacity: 0, x: 16 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.25, delay: index * 0.04 }}
          className="glass rounded-3xl px-5 py-4"
        >
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-xs uppercase tracking-[0.24em] text-zinc-500">Rank {driver.rank}</div>
              <div className="mt-2 text-lg font-semibold">{driver.fullName}</div>
              <div className="text-sm text-zinc-400">{driver.teamName}</div>
            </div>
            <div className="text-right">
              <div className="text-2xl font-semibold">{pct(driver.winProbability)}</div>
              <div className="text-xs text-zinc-500">Weather fit {driver.weatherFit.toFixed(2)}</div>
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  );
}
