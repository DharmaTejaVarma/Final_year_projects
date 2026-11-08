/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 70% Primary Background
        canvas: {
          bg: '#F4F7F6',
          section: '#EEF3F1',
          card: '#FFFFFF',
        },
        // 20% Secondary Color
        ocean: {
          DEFAULT: '#163B46',
          dark: '#163B46',
          surface: '#244F59',
          light: '#2d6370',
        },
        // 10% Accent Color
        teal: {
          DEFAULT: '#18B8A6',
          accent: '#18B8A6',
          hover: '#129889',
          light: '#e6f8f6',
        },
        // Neutrals & System
        ink: {
          primary: '#26383D',
          secondary: '#52636A',
          muted: '#829196',
          border: '#DCE6E3',
        },
        system: {
          success: '#16A36A',
          warning: '#E6A23C',
          error: '#DC5555',
        },
        // Compatibility brand colors
        brand: {
          50: '#e6f8f6',
          100: '#ccf2ed',
          200: '#99e5db',
          300: '#66d8c9',
          400: '#33cbb7',
          500: '#18B8A6',
          600: '#129889',
          700: '#0e766b',
          800: '#09554d',
          900: '#05332e',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      boxShadow: {
        soft: '0 2px 12px -2px rgba(22, 59, 70, 0.06), 0 4px 6px -2px rgba(22, 59, 70, 0.03)',
        'soft-md': '0 6px 20px -3px rgba(22, 59, 70, 0.08), 0 4px 8px -2px rgba(22, 59, 70, 0.04)',
        'soft-lg': '0 12px 30px -4px rgba(22, 59, 70, 0.09), 0 6px 12px -3px rgba(22, 59, 70, 0.05)',
        'soft-xl': '0 20px 40px -6px rgba(22, 59, 70, 0.12), 0 8px 16px -4px rgba(22, 59, 70, 0.06)',
      },
      borderRadius: {
        'xl': '12px',
        '2xl': '16px',
        '3xl': '22px',
      },
    },
  },
  plugins: [],
}
