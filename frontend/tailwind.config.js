/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        forest: {
          50:  "#f0f7f3",
          100: "#d8eedf",
          200: "#b0ddc0",
          300: "#7fc49a",
          400: "#4da872",
          500: "#2d8653",
          600: "#226644",
          700: "#1a5c38",
          800: "#12401f",
          900: "#0d2e1c",
          950: "#071810",
        }
      },
      keyframes: {
        "fade-up": {
          "0%":   { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.35s ease-out both",
      },
    },
  },
  plugins: [],
}