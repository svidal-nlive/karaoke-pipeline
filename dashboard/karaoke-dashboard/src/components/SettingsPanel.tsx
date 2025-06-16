"use client";
import { useEffect, useState } from "react";

export default function SettingsPanel() {
  const [settings, setSettings] = useState<any>({});
  const [status, setStatus] = useState("");

  useEffect(() => {
    fetch("/api/settings")
      .then((r) => r.json())
      .then(setSettings);
  }, []);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    setSettings({ ...settings, [e.target.name]: e.target.value });
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setStatus("Saving...");
    const resp = await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings)
    });
    setStatus(resp.ok ? "Saved!" : "Save failed.");
  }

  return (
    <section id="settings" className="bg-surface rounded-2xl p-8 shadow-lg border border-[#23272a]">
      <h2 className="text-xl font-semibold mb-4 text-brand">Pipeline Settings</h2>
      <form className="space-y-3" onSubmit={handleSave}>
        {Object.entries(settings).map(([key, value]) => (
          <div key={key} className="flex items-center gap-3">
            <label className="w-40 capitalize">{key.replace(/_/g, " ")}:</label>
            <input
              name={key}
              value={value}
              onChange={handleChange}
              className="flex-1 px-3 py-2 rounded bg-header border border-[#23272a] text-gray-100"
              type="text"
            />
          </div>
        ))}
        <button className="bg-brand text-white rounded px-6 py-2 font-bold shadow hover:bg-yellow-600 transition-all" type="submit">
          Save
        </button>
        {status && <div className="mt-2 text-sm text-brand">{status}</div>}
      </form>
    </section>
  );
}
