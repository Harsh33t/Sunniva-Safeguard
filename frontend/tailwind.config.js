/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        darkbg: "#090d16",
        cardbg: "#111827",
        borderline: "#1f293d",
        trustGreen: "#10b981",
        trustYellow: "#f59e0b",
        trustRed: "#ef4444"
      }
    },
  },
  plugins: [],
}
