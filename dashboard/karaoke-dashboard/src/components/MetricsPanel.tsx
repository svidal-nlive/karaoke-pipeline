"use client";
import { useEffect, useState } from "react";

export default function MetricsPanel() {
  const [metrics, setMetrics] = useState<any>(null);

  useEffect(() => {
    fetch("/api/metrics")
      .then((r) => r.json())
      .then(setMetrics)
      .catch(() => setMetrics(null));
  }, []);

  return (
    <section id="metrics" className="bg-surface rounded-2xl p-8 shadow-lg border border-[#23272a]">
      <h2 className="text-xl font-semibold mb-4 text-brand">Metrics</h2>
      {!metrics ? (
        <div>Loading metrics...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {Object.entries(metrics).map(([key, value]) => (
            <div key={key} className="p-4 bg-header rounded-lg shadow text-center">
              <div className="text-3xl font-bold text-brand">{value}</div>
              <div className="text-sm uppercase text-gray-400 mt-1">{key}</div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
