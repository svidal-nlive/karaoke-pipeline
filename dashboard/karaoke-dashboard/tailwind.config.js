/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'plex-dark': '#181818',
        'plex-primary': '#d08f33',
        'plex-accent': '#23272A',
        'plex-muted': '#6c6c6c',
        'plex-glass': 'rgba(24, 24, 24, 0.6)',
      },
      backgroundImage: {
        'plex-gradient-dark': 'linear-gradient(135deg, #23272A 0%, #181818 100%)',
        'plex-gradient-light': 'linear-gradient(135deg, #fff 0%, #f5f6fa 100%)',
      },
    },
    fontFamily: {
      sans: ['Inter', 'system-ui', 'sans-serif'],
    },
  },
  plugins: [],
};
