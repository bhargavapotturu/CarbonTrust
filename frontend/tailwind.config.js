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
          500: "#2d8653",
          700: "#1a5c38",
          900: "#0d2e1c",
        }
      }
    },
  },
  plugins: [],
}