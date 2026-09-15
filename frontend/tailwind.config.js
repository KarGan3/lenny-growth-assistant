/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Dark theme built from the requested palette: deep teal (#0F3040) as
        // the page ground, slate (#464858) for cards and controls,
        // terracotta (#A56F63) and peach (#D99B7F) as accents.
        paper: '#0F3040',
        surface: '#464858',
        ink: '#F5EFEA',
        'ink-soft': '#AEB4C4',
        muted: '#AEB4C4',
        line: 'rgba(245,239,234,0.22)',
        'line-strong': '#D99B7F',
        accent: '#D99B7F',
        'accent-strong': '#A56F63',
        'accent-wash': 'rgba(217,155,127,0.16)',
        cloud: '#A56F63',
        local: '#D99B7F',
        danger: '#E2685C',
        // Fixed dark text/icon color for content sitting on the light peach/
        // terracotta accent surfaces, which stay light-toned in this theme too.
        'on-accent': '#0F3040',
      },
      fontFamily: {
        serif: ['Newsreader', 'Georgia', 'serif'],
        sans: ['"IBM Plex Sans"', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
      },
      borderRadius: {
        sm: '6px',
        DEFAULT: '10px',
        lg: '14px',
      },
      maxWidth: {
        measure: '72ch',
      },
      keyframes: {
        blink: { '0%, 80%, 100%': { opacity: '0.25' }, '40%': { opacity: '1' } },
        'slide-in': { from: { transform: 'translateX(12px)', opacity: '0' }, to: { transform: 'translateX(0)', opacity: '1' } },
      },
      animation: {
        blink: 'blink 1.2s infinite ease-in-out',
        'slide-in': 'slide-in 180ms ease-out',
      },
      typography: ({ theme }) => ({
        DEFAULT: {
          css: {
            '--tw-prose-body': theme('colors.ink-soft'),
            '--tw-prose-headings': theme('colors.ink'),
            '--tw-prose-bold': theme('colors.ink'),
            '--tw-prose-links': theme('colors.ink'),
            '--tw-prose-bullets': theme('colors.line-strong'),
            '--tw-prose-quotes': theme('colors.ink-soft'),
            '--tw-prose-quote-borders': theme('colors.accent'),
            '--tw-prose-code': theme('colors.ink'),
            maxWidth: '72ch',
            h1: { fontFamily: theme('fontFamily.serif').join(', ') },
            h2: { fontFamily: theme('fontFamily.serif').join(', ') },
            h3: { fontFamily: theme('fontFamily.serif').join(', ') },
            code: { fontFamily: theme('fontFamily.mono').join(', '), fontWeight: '400' },
          },
        },
      }),
    },
  },
  plugins: [require('@tailwindcss/typography')],
}
