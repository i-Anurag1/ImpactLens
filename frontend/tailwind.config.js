/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0B0F17",
          900: "#10151F",
          800: "#171E2C",
          700: "#212A3D",
          600: "#2A3346",
        },
        mist: {
          100: "#E8ECF3",
          300: "#B7C0D1",
          500: "#8B94A8",
        },
        signal: {
          indigo: "#6C7BFF",
          low: "#3FBF7F",
          medium: "#E8A93B",
          high: "#E8763B",
          critical: "#E8475B",
        },
      },
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        body: ["Inter", "sans-serif"],
        mono: ["'IBM Plex Mono'", "monospace"],
      },
      borderRadius: {
        sm: "4px",
      },
    },
  },
  plugins: [],
};
