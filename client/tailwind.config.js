/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        cyber: {
          bg: "#080c14",
          surface: "#0f172a",
          card: "rgba(15, 23, 42, 0.75)",
          border: "rgba(56, 189, 248, 0.2)",
          cyan: "#00f0ff",
          emerald: "#10b981",
          quantum: "#00ffaa",
          amber: "#f59e0b",
          red: "#ff2a5f",
          purple: "#a855f7",
        }
      },
      animation: {
        'pulse-glow': 'pulseGlow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'quantum-spin': 'spin 8s linear infinite',
        'scanline': 'scanline 4s linear infinite',
      },
      keyframes: {
        pulseGlow: {
          '0%, 100%': { opacity: '1', filter: 'drop-shadow(0 0 15px rgba(0, 255, 170, 0.6))' },
          '50%': { opacity: '0.6', filter: 'drop-shadow(0 0 5px rgba(0, 255, 170, 0.2))' },
        },
        scanline: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(1000%)' },
        }
      },
      boxShadow: {
        'neon-cyan': '0 0 20px rgba(0, 240, 255, 0.35)',
        'neon-green': '0 0 25px rgba(0, 255, 170, 0.45)',
        'neon-red': '0 0 20px rgba(255, 42, 95, 0.4)',
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.5)',
      }
    },
  },
  plugins: [],
}
