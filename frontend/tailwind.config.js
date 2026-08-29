/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        paper: {
          DEFAULT: "var(--paper)",
          subtle: "var(--canvas-subtle)",
        },
        ink: {
          DEFAULT: "var(--ink)",
          secondary: "var(--ink-secondary)",
          muted: "var(--ink-muted)",
        },
        accent: {
          coral: "var(--accent-coral)",
          "coral-hover": "var(--accent-coral-hover)",
        },
        pastel: {
          mint: "var(--pastel-mint)",
          lilac: "var(--pastel-lilac)",
          yellow: "var(--pastel-yellow)",
          sky: "var(--pastel-sky)",
        },
      },
      fontFamily: {
        serif: ["Fraunces", "Georgia", "serif"],
        sans: ["Plus Jakarta Sans", "Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      boxShadow: {
        tactile: "2px 3px 0px var(--ink)",
        "tactile-sm": "1px 2px 0px var(--ink)",
        "tactile-lg": "4px 5px 0px var(--ink)",
      },
      borderRadius: {
        card: "10px",
      },
    },
  },
  plugins: [],
}
