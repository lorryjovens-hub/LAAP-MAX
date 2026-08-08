/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './src/**/*.{js,ts,jsx,tsx}',
    './electron/**/*.{js,ts}',
    './public/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        'laap-bg-primary': '#050608',
        'laap-bg-secondary': '#0a0a10',
        'laap-bg-tertiary': '#111118',
        'laap-accent': '#7c7cff',
        'laap-accent-light': '#a07cff',
        'laap-secondary': '#00f5d4',
        'laap-text-primary': '#f5f5f7',
        'laap-text-secondary': 'rgba(255, 255, 255, 0.6)',
        'laap-text-tertiary': 'rgba(255, 255, 255, 0.4)',
        'laap-status-ok': '#00f5d4',
        'laap-status-error': '#ff6b6b',
        'laap-status-warn': '#ffd166',
        'laap-status-info': '#7c7cff',
        'laap-warn': '#f7b801',
      },
      fontFamily: {
        sans: ['"Inter"', '"PingFang SC"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Geist Mono"', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [],
}
