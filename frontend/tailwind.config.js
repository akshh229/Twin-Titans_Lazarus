/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'lazarus-bg': '#10141a',
        'lazarus-surface-low': '#0a0e14',
        'lazarus-surface': '#1c2026',
        'lazarus-surface-high': '#31353c',
        'lazarus-border': '#424754',
        'lazarus-text': '#e2e8f0',
        'lazarus-muted': '#94a3b8',
        'lazarus-critical': '#ef4444',
        'lazarus-warning': '#f59e0b',
        'lazarus-normal': '#10b981',
        'lazarus-info': '#3b82f6',
        'lazarus-accent': '#4d8eff',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
      boxShadow: {
        'glow-critical': '0 0 15px rgba(239, 68, 68, 0.3)',
      }
    },
  },
  plugins: [],
}
