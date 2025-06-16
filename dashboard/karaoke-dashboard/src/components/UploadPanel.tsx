"use client";
import { useRef, useState } from "react";

export default function UploadPanel() {
  const [status, setStatus] = useState("");
  const fileInput = useRef<HTMLInputElement>(null);

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!fileInput.current?.files?.[0]) return;
    setStatus("Uploading...");
    const formData = new FormData();
    formData.append("file", fileInput.current.files[0]);
    try {
      const resp = await fetch("/api/upload", { method: "POST", body: formData });
      setStatus(resp.ok ? "Upload successful!" : "Upload failed.");
    } catch {
      setStatus("Upload error.");
    }
  }

  return (
    <section id="upload" className="bg-surface rounded-2xl p-8 shadow-lg border border-[#23272a]">
      <h2 className="text-xl font-semibold mb-4 text-brand">Upload File</h2>
      <form className="flex items-center gap-4" onSubmit={handleUpload}>
        <input
          ref={fileInput}
          type="file"
          className="block text-sm text-gray-300 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-brand file:text-white hover:file:bg-yellow-500"
          required
        />
        <button
          className="bg-brand text-white rounded px-6 py-2 font-bold shadow hover:bg-yellow-600 transition-all"
          type="submit"
        >
          Upload
        </button>
      </form>
      {status && <div className="mt-3 text-sm text-brand">{status}</div>}
    </section>
  );
}
