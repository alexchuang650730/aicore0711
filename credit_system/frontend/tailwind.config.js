/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    './pages/**/*.{js,jsx}',
    './components/**/*.{js,jsx}',
    './app/**/*.{js,jsx}',
    './src/**/*.{js,jsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // PowerAutomation 品牌顏色
        brand: {
          50: '#f0f4ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          800: '#3730a3',
          900: '#312e81',
        },
        // AI-UI 智能顏色
        smart: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: 0 },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: 0 },
        },
        "fade-in": {
          from: { opacity: 0, transform: "translateY(10px)" },
          to: { opacity: 1, transform: "translateY(0)" },
        },
        "slide-in": {
          from: { transform: "translateX(-100%)" },
          to: { transform: "translateX(0)" },
        },
        "bounce-in": {
          "0%": { transform: "scale(0.3)", opacity: 0 },
          "50%": { transform: "scale(1.05)", opacity: 0.8 },
          "100%": { transform: "scale(1)", opacity: 1 },
        },
        "pulse-smart": {
          "0%, 100%": { opacity: 1 },
          "50%": { opacity: 0.5 },
        },
        "gradient-x": {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "fade-in": "fade-in 0.5s ease-out",
        "slide-in": "slide-in 0.3s ease-out",
        "bounce-in": "bounce-in 0.6s ease-out",
        "pulse-smart": "pulse-smart 2s ease-in-out infinite",
        "gradient-x": "gradient-x 3s ease infinite",
      },
      // 響應式字體
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1rem' }],
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],
        'base': ['1rem', { lineHeight: '1.5rem' }],
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],
        'xl': ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
        '5xl': ['3rem', { lineHeight: '1' }],
        '6xl': ['3.75rem', { lineHeight: '1' }],
        '7xl': ['4.5rem', { lineHeight: '1' }],
        '8xl': ['6rem', { lineHeight: '1' }],
        '9xl': ['8rem', { lineHeight: '1' }],
      },
      // 響應式間距
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '120': '30rem',
      },
      // 適配不同屏幕的斷點
      screens: {
        'xs': '475px',
        'sm': '640px',
        'md': '768px',
        'lg': '1024px',
        'xl': '1280px',
        '2xl': '1536px',
        '3xl': '1920px',
        // 移動設備優先
        'mobile': { 'max': '767px' },
        'tablet': { 'min': '768px', 'max': '1023px' },
        'desktop': { 'min': '1024px' },
      },
    },
  },
  plugins: [
    require("tailwindcss-animate"),
    // 自定義插件：智能響應式工具
    function({ addUtilities, theme }) {
      const newUtilities = {
        '.smart-container': {
          'max-width': '100%',
          'padding-left': '1rem',
          'padding-right': '1rem',
          'margin-left': 'auto',
          'margin-right': 'auto',
          '@media (min-width: 640px)': {
            'max-width': '640px',
            'padding-left': '1.5rem',
            'padding-right': '1.5rem',
          },
          '@media (min-width: 768px)': {
            'max-width': '768px',
            'padding-left': '2rem',
            'padding-right': '2rem',
          },
          '@media (min-width: 1024px)': {
            'max-width': '1024px',
          },
          '@media (min-width: 1280px)': {
            'max-width': '1280px',
          },
        },
        '.smart-grid': {
          'display': 'grid',
          'grid-template-columns': 'repeat(1, minmax(0, 1fr))',
          'gap': '1rem',
          '@media (min-width: 640px)': {
            'grid-template-columns': 'repeat(2, minmax(0, 1fr))',
          },
          '@media (min-width: 1024px)': {
            'grid-template-columns': 'repeat(3, minmax(0, 1fr))',
          },
          '@media (min-width: 1280px)': {
            'grid-template-columns': 'repeat(4, minmax(0, 1fr))',
          },
        },
        '.smart-text': {
          'font-size': '0.875rem',
          'line-height': '1.25rem',
          '@media (min-width: 640px)': {
            'font-size': '1rem',
            'line-height': '1.5rem',
          },
          '@media (min-width: 1024px)': {
            'font-size': '1.125rem',
            'line-height': '1.75rem',
          },
        },
        '.smart-padding': {
          'padding': '1rem',
          '@media (min-width: 640px)': {
            'padding': '1.5rem',
          },
          '@media (min-width: 1024px)': {
            'padding': '2rem',
          },
        },
        '.glass-effect': {
          'background': 'rgba(255, 255, 255, 0.1)',
          'backdrop-filter': 'blur(10px)',
          'border': '1px solid rgba(255, 255, 255, 0.2)',
          'box-shadow': '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
        },
        '.gradient-brand': {
          'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        },
        '.gradient-smart': {
          'background': 'linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%)',
        },
      }
      
      addUtilities(newUtilities, ['responsive', 'hover'])
    },
  ],
}