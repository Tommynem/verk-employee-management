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
      screens: {
        'xs': '375px',
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
          // VaWW Primary Orange - oklch format
          primary: "oklch(0.74 0.17 60)",
          "primary-content": "oklch(1 0 0)",

          // Secondary
          secondary: "oklch(0.55 0.01 260)",
          "secondary-content": "oklch(1 0 0)",

          // Accent
          accent: "oklch(0.65 0.20 290)",
          "accent-content": "oklch(1 0 0)",

          // Neutral base colors (light theme)
          "base-100": "oklch(0.97 0.005 260)",
          "base-200": "oklch(0.92 0.008 260)",
          "base-300": "oklch(0.82 0.012 260)",
          "base-content": "oklch(0.20 0.01 260)",

          // Semantic colors
          success: "oklch(0.55 0.20 145)",
          "success-content": "oklch(1 0 0)",
          warning: "oklch(0.70 0.15 80)",
          "warning-content": "oklch(0.15 0 0)",
          error: "oklch(0.55 0.24 25)",
          "error-content": "oklch(1 0 0)",
          info: "oklch(0.55 0.20 240)",
          "info-content": "oklch(1 0 0)",

          // Neutral
          neutral: "oklch(0.55 0.01 260)",
          "neutral-content": "oklch(1 0 0)",

          // UI styling
          "--rounded-box": "0.5rem",
          "--rounded-btn": "0.25rem",
          "--rounded-badge": "1rem",
        },
      },
    ],
    darkTheme: false,
    base: true,
    styled: true,
    utils: true,
    logs: false,
  },
}
