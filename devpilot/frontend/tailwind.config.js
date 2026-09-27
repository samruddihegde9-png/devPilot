/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0B0E14",
          900: "#0F131B",
          850: "#131822",
          800: "#181E2A",
          700: "#212836",
          600: "#2B3345",
          500: "#3B4459",
          400: "#5B6580",
          300: "#8891A6",
          200: "#B4BBCB",
          100: "#DDE1EA",
        },
        amber: {
          400: "#F0B45B",
          500: "#E8A33D",
          600: "#C6812A",
        },
        signal: {
          green: "#5FBF87",
          red: "#E1626B",
          blue: "#5B9FE8",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        panel: "0 0 0 1px rgba(255,255,255,0.04)",
      },
    },
  },
  plugins: [],
};
