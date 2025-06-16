import { NextResponse } from 'next/server'

export async function GET() {
  // Replace with real backend call later
  return NextResponse.json({
    filesProcessed: 123,
    activeJobs: 2,
    queuedFiles: 4,
    failedJobs: 0,
  })
}
