"use client";
import { useEffect, useState } from "react";
import { Sun, Moon } from "lucide-react";

export default function ThemeToggle() {
  const [dark, setDark] = useState(true);

  useEffect(() => {
    if (dark) {
      document.documentElement.setAttribute("data-theme", "dark");
    } else {
      document.documentElement.setAttribute("data-theme", "light");
    }
  }, [dark]);

  return (
    <button
      className="flex items-center gap-2 px-4 py-2 rounded-lg bg-plex-glass text-plex-primary border border-plex-primary shadow transition-all hover:bg-plex-primary hover:text-plex-dark"
      onClick={() => setDark((d) => !d)}
      aria-label="Toggle theme"
      type="button"
    >
      {dark ? <Sun size={20} /> : <Moon size={20} />}
      {dark ? "Day Mode" : "Night Mode"}
    </button>
  );
}
