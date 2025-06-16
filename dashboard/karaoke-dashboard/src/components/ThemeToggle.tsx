"use client";
import { useEffect, useState } from "react";
import { Sun, Moon } from "lucide-react";

export default function ThemeToggle() {
  const [dark, setDark] = useState(true);

  useEffect(() => {
    if (dark) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [dark]);

  return (
    <button
      className="flex items-center gap-2 px-3 py-2 rounded bg-surface hover:bg-header border border-brand text-brand font-medium transition-all"
      onClick={() => setDark((d) => !d)}
      aria-label="Toggle theme"
      type="button"
    >
      {dark ? <Sun size={18} /> : <Moon size={18} />}
      {dark ? "Day Mode" : "Dark Mode"}
    </button>
  );
}
