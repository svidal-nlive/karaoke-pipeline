import { NextRequest, NextResponse } from 'next/server'

export async function POST(req: NextRequest) {
  // For now, just accept and pretend to process the file
  // In production, forward to your backend API or save to storage
  return NextResponse.json({ ok: true })
}
