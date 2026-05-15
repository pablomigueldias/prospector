import { CSSProperties } from 'react';

interface BrandMarkProps {
  size?: number;
  color?: string;
  className?: string;
  animate?: boolean;
}

export function BrandMark({
  size = 28,
  color,
  className,
  animate = false,
}: BrandMarkProps) {
  const orbitStyle: CSSProperties | undefined = animate
    ? {
        transformOrigin: 'center',
        animation: 'reativa-spin 6s linear infinite',
      }
    : undefined;

  return (
    <>
      <svg
        width={size}
        height={size}
        viewBox="0 0 64 64"
        fill="none"
        className={className}
        aria-label="Reative Systems"
        role="img"
      >
        <ellipse
          cx="32"
          cy="32"
          rx="28"
          ry="10"
          stroke={color ?? 'oklch(0.68 0.19 38)'}
          strokeWidth="2.5"
          transform="rotate(-18 32 32)"
          fill="none"
        />
        <ellipse
          cx="32"
          cy="32"
          rx="28"
          ry="10"
          stroke={color ?? 'oklch(0.68 0.19 38)'}
          strokeWidth="1"
          transform="rotate(-18 32 32)"
          fill="none"
          opacity="0.5"
          strokeDasharray="2 4"
          style={orbitStyle}
        />
        <path
          d="M18 16h12.5c5.2 0 9 3.6 9 8.4 0 3.7-2.2 6.7-5.6 7.9L41 48h-7.6l-6.3-14.4H24V48h-6V16zm6 5.4v6.8h6c2.4 0 4.1-1.4 4.1-3.4s-1.7-3.4-4.1-3.4H24z"
          fill="currentColor"
        />
      </svg>
      <style jsx>{`
        @keyframes reativa-spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </>
  );
}
