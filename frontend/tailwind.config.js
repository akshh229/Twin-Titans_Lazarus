/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'lazarus-bg': '#091019',
        'lazarus-surface-low': '#0f1822',
        'lazarus-surface': '#15202c',
        'lazarus-surface-high': '#203040',
        'lazarus-border': '#314255',
        'lazarus-text': '#f4efe6',
        'lazarus-muted': '#96a6bb',
        'lazarus-critical': '#f06c66',
        'lazarus-warning': '#f1b15e',
        'lazarus-normal': '#4bc58f',
        'lazarus-info': '#8db4ff',
        'lazarus-accent': '#8aa8ff',
      },
      fontFamily: {
        sans: ['Manrope', 'system-ui', 'sans-serif'],
        display: ['Cormorant Garamond', 'Georgia', 'serif'],
        mono: ['IBM Plex Mono', 'Consolas', 'monospace'],
      },
      boxShadow: {
        'glow-critical': '0 0 15px rgba(239, 68, 68, 0.3)',
      }
    },
  },
  plugins: [],
}
