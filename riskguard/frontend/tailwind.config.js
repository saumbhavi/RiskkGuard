/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        paper: '#F5F6F8',
        surface: '#FFFFFF',
        ink: {
          DEFAULT: '#14171C',
          muted: '#5B6472',
          faint: '#8A93A3',
        },
        line: '#DEE1E6',
        brand: {
          DEFAULT: '#1B4D3E',
          dark: '#123529',
          light: '#E7EFEC',
        },
        risk: {
          low: '#2F7D5B',
          lowBg: '#EAF4EE',
          medium: '#B8862B',
          mediumBg: '#FBF2E2',
          high: '#B23A34',
          highBg: '#FBEAE9',
        },
      },
      fontFamily: {
        display: ['"Fraunces"', 'serif'],
        sans: ['"IBM Plex Sans"', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'monospace'],
      },
      borderRadius: {
        sm: '4px',
        DEFAULT: '6px',
      },
    },
  },
  plugins: [],
}
