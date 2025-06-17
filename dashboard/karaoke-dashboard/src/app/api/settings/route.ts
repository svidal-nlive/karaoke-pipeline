import { NextRequest, NextResponse } from 'next/server';

const STATUS_API = process.env.STATUS_API_URL || "http://status-api:5001";

export async function GET() {
  const resp = await fetch(`${STATUS_API}/status`);
  if (!resp.ok) return NextResponse.json({}, { status: 500 });
  // TODO: Adjust this endpoint based on your status-api's settings endpoint (or create one)
  // Return mock data for now:
  return NextResponse.json({
    chunkLengthMs: 60000,
    stemType: "accompaniment"
  });
}

export async function POST(req: NextRequest) {
  const body = await req.json();
  // TODO: Forward to status-api if you add a settings endpoint
  return NextResponse.json({ ok: true });
}
