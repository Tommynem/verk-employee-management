/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./templates/**/*.html",
    "./static/**/*.js",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Open Sans', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      colors: {
        brand: {
          orange: '#f68d0f',
          'orange-dark': '#e67e00',
          'dark-start': '#1e2939',
          'dark-end': '#364153',
        },
      },
    },
  },
  plugins: [
    require("daisyui"),
  ],
  daisyui: {
    themes: [
      {
        verk: {
          "primary": "#f68d0f",           // Brand orange
          "primary-content": "#ffffff",   // White text on primary
          "secondary": "#1e2939",         // Brand dark
          "secondary-content": "#ffffff",
          "accent": "#e67e00",            // Brand orange dark
          "neutral": "#1f2937",
          "base-100": "#ffffff",
          "base-200": "#f3f4f6",
          "base-300": "#e5e7eb",
          "info": "#3b82f6",
          "success": "#00a63e",           // From design tokens
          "warning": "#bb4d00",           // From design tokens
          "error": "#e7000b",             // From design tokens
        },
      },
    ],
  },
}
