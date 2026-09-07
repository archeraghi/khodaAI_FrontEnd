/** @type {import('tailwindcss').Config} */
module.exports = {
  content: {
    relative: true,
    files: ["./index.html"],
  },
  theme: {
    extend: {
      fontFamily: { sans: ["Inter", "ui-sans-serif", "system-ui"] },
      colors: {
        kh: {
          dark: "#5B0E14",
          base: "#8E1C24",
          bright: "#C62832",
          blush: "#F9E9EB",
          ink: "#0B0B0C",
          mute: "#6B6E77",
        },
      },
      boxShadow: {
        glow: "0 10px 30px -10px rgba(198,40,50,.35)",
      },
    },
  },
  plugins: [],
};
