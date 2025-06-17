'use client';
import { useState, useEffect } from "react";
import UploadPanel from "@/components/UploadPanel";
import MetricsPanel from "@/components/MetricsPanel";
import SettingsPanel from "@/components/SettingsPanel";
import { Sun, Moon } from "lucide-react";

export default function DashboardPage() {
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');

  useEffect(() => {
    document.body.setAttribute('data-theme', theme);
  }, [theme]);

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)", color: "var(--fg)" }}>
      <header style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '1rem 2rem',
        background: 'var(--secondary)'
      }}>
        <h1 style={{ margin: 0, fontSize: "1.5rem", color: "var(--accent)" }}>Karaoke Pipeline</h1>
        <button
          id="theme-toggle"
          aria-label="Toggle theme"
          style={{ fontSize: "1.5rem", cursor: "pointer", background: "none", border: "none", color: "var(--fg)" }}
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
        >
          {theme === "dark" ? "🌙" : "☀️"}
        </button>
      </header>
      <main className="dashboard-container" style={{ padding: '2rem' }}>
        <section className="glass-card upload-section">
          <UploadPanel />
        </section>
        <section className="glass-card">
          <MetricsPanel />
        </section>
        <section className="glass-card settings-section">
          <SettingsPanel />
        </section>
      </main>
      <footer style={{
        background: 'var(--secondary)',
        padding: '1rem',
        textAlign: 'center',
        color: '#888'
      }}>
        &copy; {new Date().getFullYear()} Karaoke Pipeline
      </footer>
    </div>
  );
}
