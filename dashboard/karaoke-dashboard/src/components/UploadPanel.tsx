"use client";
import { useRef, useState } from "react";
import { UploadCloud } from "lucide-react";

export default function UploadPanel() {
  const fileInput = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!fileInput.current?.files?.[0]) return;
    setUploading(true);
    setMessage(null);
    const formData = new FormData();
    formData.append("file", fileInput.current.files[0]);
    try {
      const res = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });
      if (res.ok) setMessage("File uploaded!");
      else setMessage("Upload failed.");
    } catch {
      setMessage("Upload error.");
    }
    setUploading(false);
  }

  return (
    <>
      <h2>Upload File</h2>
      <form className="flex flex-col gap-3" onSubmit={handleUpload}>
        <input
          type="file"
          ref={fileInput}
          className="file:bg-[var(--accent)] file:text-white file:rounded file:p-2 bg-[var(--input-bg)] text-[var(--fg)] p-2 rounded"
          accept=".mp3,.wav"
        />
        <button
          type="submit"
          style={{
            background: "var(--accent)",
            color: "#000",
            border: "none",
            padding: "0.6rem 1.2rem",
            borderRadius: 5,
            fontWeight: "bold",
            cursor: "pointer",
          }}
          disabled={uploading}
        >
          <UploadCloud className="inline mr-1" size={18} />
          {uploading ? "Uploading..." : "Upload"}
        </button>
        {message && (
          <div style={{ marginTop: 8, color: "var(--accent)" }}>{message}</div>
        )}
      </form>
    </>
  );
}
