/** @type {import('tailwindcss').Config} */
// Palette ported verbatim from web/.web_ref/pstmain/styles/colors.py (dark navy + blue/cyan).
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Background surfaces (deep navy)
        bg: {
          base: '#0A0E1A',
          deep: '#0F1621',
          surface: '#121926',
          hover: '#1A2332',
          elevated: '#1E2633',
          card: '#161E2D',
        },
        // Primary accent (blue) + cyan secondary
        accent: {
          DEFAULT: '#3B8ED0',
          light: '#5BA3E0',
          dark: '#2B7EB8',
          secondary: '#1E88E5',
          cyan: '#00BCD4',
        },
        // Status semantics
        status: {
          success: '#4CAF50',
          warning: '#FFD24D',
          error: '#F44336',
          info: '#2196F3',
          amber: '#FFB74D',
          'amber-dark': '#FF9800',
        },
        // Text ink
        ink: {
          primary: '#E3F2FD',
          secondary: '#B0BEC5',
          muted: '#78909C',
          dim: '#546E7A',
          inverse: '#0A0E1A',
          emphasis: '#FFFFFF',
        },
        // Borders / dividers
        line: {
          DEFAULT: '#1E2633',
          hover: '#2D3A4E',
          focus: '#3B8ED0',
        },
        // Accent headers used on chips/badges
        header: {
          purple: '#A78BFA',
          sky: '#7DD3FC',
          green: '#22C55E',
          discord: '#5865F2',
        },
      },
      fontFamily: {
        sans: ['system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['"Hack Nerd Font"', 'ui-monospace', 'Consolas', 'Liberation Mono', 'Menlo', 'monospace'],
      },
      borderRadius: {
        '4': '4px',
        '6': '6px',
        '8': '8px',
        '12': '12px',
      },
      boxShadow: {
        'glow': '0 0 20px rgba(59, 142, 208, 0.3)',
        'glow-strong': '0 0 30px rgba(59, 142, 208, 0.5)',
        'card': '0 4px 6px rgba(0, 0, 0, 0.4)',
        'card-lg': '0 10px 15px rgba(0, 0, 0, 0.5)',
      },
      transitionDuration: {
        'fast': '150ms',
        'normal': '250ms',
        'slow': '350ms',
      },
      backgroundImage: {
        'surface-gradient': 'linear-gradient(180deg, #0A0E1A 0%, #0F1621 100%)',
        'header-gradient': 'linear-gradient(90deg, #0A0E1A 0%, #121926 100%)',
        'nav-gradient': 'linear-gradient(180deg, rgba(18, 25, 38, 0.98) 0%, rgba(10, 14, 26, 0.98) 100%)',
        'card-gradient': 'linear-gradient(145deg, #161E2D 0%, #121926 100%)',
        'accent-gradient': 'linear-gradient(135deg, #1E88E5 0%, #3B8ED0 50%, #00BCD4 100%)',
        'stats-gradient': 'linear-gradient(180deg, #3B8ED0 0%, #00BCD4 100%)',
        'selection-gradient': 'linear-gradient(180deg, #FFB74D 0%, #FF9800 100%)',
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        fadeIn: { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        slideUp: { '0%': { opacity: '0', transform: 'translateY(8px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
        pulseGlow: {
          '0%': { boxShadow: '0 0 12px rgba(59, 142, 208, 0.2)' },
          '100%': { boxShadow: '0 0 24px rgba(59, 142, 208, 0.45)' },
        },
      },
    },
  },
  plugins: [],
};
