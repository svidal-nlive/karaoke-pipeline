"use client";
import { useEffect, useState } from "react";

type Settings = {
  chunkLengthMs: number;
  stemType: string;
};

export default function SettingsPanel() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetch("/api/settings")
      .then((r) => r.json())
      .then(setSettings)
      .catch(() => setSettings(null));
  }, []);

  function updateField(field: keyof Settings, value: any) {
    setSettings((prev) => prev ? { ...prev, [field]: value } : prev);
  }

  async function saveSettings(e: React.FormEvent) {
    e.preventDefault();
    if (!settings) return;
    setSaving(true);
    try {
      await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settings),
      });
    } finally {
      setSaving(false);
    }
  }

  if (!settings) {
    return <div>Loading...</div>;
  }

  return (
    <>
      <h2>Pipeline Settings</h2>
      <form className="settings-form" onSubmit={saveSettings}>
        <label htmlFor="chunkLength">Chunk Length (ms)</label>
        <input
          type="number"
          id="chunkLength"
          name="chunkLength"
          value={settings.chunkLengthMs}
          min={1000}
          step={1000}
          onChange={e => updateField('chunkLengthMs', Number(e.target.value))}
        />

        <label htmlFor="stemType">Stem Type</label>
        <select
          id="stemType"
          name="stemType"
          value={settings.stemType}
          onChange={e => updateField('stemType', e.target.value)}
        >
          <option value="accompaniment">Accompaniment</option>
          <option value="vocals">Vocals</option>
          <option value="both">Both</option>
        </select>

        <button type="submit" disabled={saving}>
          {saving ? "Saving..." : "Save Settings"}
        </button>
      </form>
    </>
  );
}
