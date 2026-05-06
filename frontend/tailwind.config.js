export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: "#eff6ff",
          100: "#dbeafe",
          500: "#3b82f6",
          700: "#1d4ed8",
          900: "#1e3a8a"
        },
        success: "#10b981",
        warning: "#f59e0b",
        danger: "#ef4444",
        surface: "#ffffff",
        background: "#f8fafc",
        text: "#0f172a"
      },
    },
  },
  plugins: [],
};