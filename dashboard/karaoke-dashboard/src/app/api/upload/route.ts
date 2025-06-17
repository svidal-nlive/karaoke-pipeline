import { NextRequest, NextResponse } from 'next/server';

const STATUS_API = process.env.STATUS_API_URL || "http://status-api:5001";

export async function POST(req: NextRequest) {
  const formData = await req.formData();
  const file = formData.get("file");
  if (!(file instanceof Blob)) {
    return NextResponse.json({ error: "No file uploaded" }, { status: 400 });
  }

  // Proxy file upload to status-api /input endpoint
  const backendForm = new FormData();
  backendForm.append("file", file, "upload.mp3");
  const uploadResp = await fetch(`${STATUS_API}/input`, {
    method: "POST",
    body: backendForm,
  });

  if (!uploadResp.ok) {
    return NextResponse.json({ error: "Backend upload failed" }, { status: 500 });
  }
  const json = await uploadResp.json();
  return NextResponse.json(json);
}
