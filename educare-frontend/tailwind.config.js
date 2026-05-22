/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        educare: {
          primary: '#2563eb',
          secondary: '#f3f4f6',
          accent: '#14b8a6',
          warning: '#f59e0b',
          text: '#374151',
          muted: '#9ca3af',
        },
      },
    },
  },
  plugins: [],
};
