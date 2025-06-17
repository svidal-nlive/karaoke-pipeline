"use client";
import { useEffect, useState } from "react";

type Metrics = {
  filesProcessed: number;
  totalJobs: number;
  queuedFiles: number;
  failedJobs: number;
};

export default function MetricsPanel() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);

  useEffect(() => {
    fetch("/api/metrics")
      .then((r) => r.json())
      .then(setMetrics)
      .catch(() => setMetrics(null));
  }, []);

  return (
    <>
      <h2>Pipeline Metrics</h2>
      <div className="metrics">
        <div className="metric">
          <h3>Files Processed</h3>
          <p id="filesProcessed">{metrics ? metrics.filesProcessed : 0}</p>
        </div>
        <div className="metric">
          <h3>Total Jobs</h3>
          <p id="totalJobs">{metrics ? metrics.totalJobs : 0}</p>
        </div>
        <div className="metric">
          <h3>Queued Files</h3>
          <p id="queuedFiles">{metrics ? metrics.queuedFiles : 0}</p>
        </div>
        <div className="metric">
          <h3>Failed</h3>
          <p id="failedJobs">{metrics ? metrics.failedJobs : 0}</p>
        </div>
      </div>
    </>
  );
}
