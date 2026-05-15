import type { Config } from 'tailwindcss';

/**
 * Design system da Reative Systems espelhado em utilitários Tailwind.
 *
 * As cores aqui são as MESMAS variáveis OKLCH do styles.css do site
 * principal — então `bg-brand` no React renderiza exatamente como
 * `background: var(--brand)` no site. Identidade visual idêntica.
 */
const config: Config = {
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './lib/**/*.{ts,tsx}',
    './hooks/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // ── Warm neutral base ────────────────────────────────────────
        bg: 'oklch(0.985 0.005 60)',
        'bg-alt': 'oklch(0.965 0.008 60)',
        surface: 'oklch(1 0 0)',
        // ── Tinta (texto) ────────────────────────────────────────────
        ink: 'oklch(0.16 0.015 50)',
        'ink-soft': 'oklch(0.32 0.012 50)',
        'ink-mute': 'oklch(0.5 0.012 50)',
        'ink-faint': 'oklch(0.7 0.01 60)',
        // ── Bordas ───────────────────────────────────────────────────
        line: 'oklch(0.9 0.008 60)',
        'line-soft': 'oklch(0.94 0.006 60)',
        // ── Marca (laranja) ──────────────────────────────────────────
        brand: {
          DEFAULT: 'oklch(0.68 0.19 38)',
          deep: 'oklch(0.6 0.2 35)',
          soft: 'oklch(0.94 0.04 50)',
          ink: 'oklch(0.32 0.14 38)',
        },
        // ── Superfícies escuras (pra dark spots / hero) ──────────────
        dark: {
          DEFAULT: 'oklch(0.16 0.015 50)',
          alt: 'oklch(0.21 0.015 50)',
          line: 'oklch(0.28 0.012 50)',
        },
        'on-dark': 'oklch(0.97 0.005 60)',
        'on-dark-soft': 'oklch(0.75 0.012 50)',
        // ── Semânticas ───────────────────────────────────────────────
        success: 'oklch(0.55 0.12 145)',
        'success-soft': 'oklch(0.94 0.06 145)',
        'success-ink': 'oklch(0.35 0.1 145)',
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        body: ['Manrope', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: [
          '"JetBrains Mono"',
          'ui-monospace',
          'SFMono-Regular',
          'Menlo',
          'monospace',
        ],
      },
      fontSize: {
        // Type scale da Reativa
        eyebrow: ['12px', { lineHeight: '1.3', letterSpacing: '0.12em' }],
      },
      borderRadius: {
        sm: '6px',
        DEFAULT: '10px',
        lg: '16px',
        xl: '24px',
        pill: '999px',
      },
      boxShadow: {
        sm: '0 1px 2px oklch(0 0 0 / 0.04), 0 0 0 1px oklch(0 0 0 / 0.04)',
        DEFAULT:
          '0 4px 16px -4px oklch(0 0 0 / 0.08), 0 0 0 1px oklch(0 0 0 / 0.05)',
        lg: '0 24px 48px -16px oklch(0 0 0 / 0.18), 0 0 0 1px oklch(0 0 0 / 0.05)',
        brand: '0 12px 32px -8px oklch(0.68 0.19 38 / 0.35)',
        'brand-sm': '0 8px 24px -8px oklch(0.68 0.19 38 / 0.4)',
        focus: '0 0 0 3px oklch(0.68 0.19 38 / 0.15)',
      },
      letterSpacing: {
        tightest: '-0.035em',
        tighter: '-0.028em',
        tight: '-0.02em',
      },
      transitionTimingFunction: {
        snap: 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
      backdropBlur: {
        nav: '16px',
      },
    },
  },
  plugins: [],
};

export default config;
