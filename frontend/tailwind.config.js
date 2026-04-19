/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Catppuccin Mocha 深色主题
        'ctp-base': '#1e1e2e',
        'ctp-mantle': '#181825',
        'ctp-crust': '#11111b',
        'ctp-surface': '#313244',
        'ctp-overlay': '#45475a',
        'ctp-text': '#cdd6f4',
        'ctp-subtext': '#a6adc8',
        'ctp-blue': '#89b4fa',
        'ctp-green': '#a6e3a1',
        'ctp-orange': '#fab387',
        'ctp-pink': '#f38ba8',
        'ctp-teal': '#94e2d5',
      },
    },
  },
  plugins: [],
}