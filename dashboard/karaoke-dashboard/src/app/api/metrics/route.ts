import { NextResponse } from 'next/server';

const STATUS_API = process.env.STATUS_API_URL || "http://status-api:5001";

export async function GET() {
  const resp = await fetch(`${STATUS_API}/pipeline-health`);
  if (!resp.ok) return NextResponse.json({}, { status: 500 });
  const data = await resp.json();
  // Adapt keys to what MetricsPanel expects
  return NextResponse.json({
    filesProcessed: (data.queued ?? 0) + (data.organized ?? 0),
    totalJobs: Object.values(data).reduce((a, b) => a + b, 0),
    queuedFiles: data.queued ?? 0,
    failedJobs: data.error ?? 0,
  });
}
