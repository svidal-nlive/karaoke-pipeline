/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'plex-dark': '#181818',
        'plex-primary': '#d08f33', // your logo gold
        'plex-accent': '#23272A',
      },
    },
  },
  plugins: [],
};
