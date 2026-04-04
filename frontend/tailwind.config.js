/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#132238",
        sand: "#f5efe2",
        ember: "#d97706",
        mist: "#edf3fb",
      },
      boxShadow: {
        panel: "0 24px 60px rgba(19, 34, 56, 0.08)",
      },
      backgroundImage: {
        "hero-wash":
          "radial-gradient(circle at top left, rgba(255, 236, 179, 0.92), transparent 32%), linear-gradient(145deg, #f6fbff 0%, #ecf4ff 42%, #fff9ef 100%)",
      },
    },
  },
  plugins: [],
};
