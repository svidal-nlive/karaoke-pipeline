import { NextRequest, NextResponse } from 'next/server'

let mockSettings = {
  chunkLengthMs: 60000,
  stemType: 'accompaniment',
}

export async function GET() {
  // Replace with real backend call later
  return NextResponse.json(mockSettings)
}

export async function POST(req: NextRequest) {
  const body = await req.json()
  mockSettings = body // Persist only in-memory
  return NextResponse.json({ ok: true })
}
