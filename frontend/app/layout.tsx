import type { Metadata } from "next";

import "@/app/globals.css";

export const metadata: Metadata = {
  title: "F1 Winner Prediction",
  description: "Predict the next Formula 1 race winner using FastF1 and weather signals.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

