import type { SVGProps } from 'react';

type IconBase = SVGProps<SVGSVGElement>;

const baseProps: IconBase = {
  width: '1em',
  height: '1em',
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.75,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
};


export function IconRadar(p: IconBase) {
  return (
    <svg {...baseProps} {...p}>
      <path d="M19.07 4.93A10 10 0 0 0 6.99 3.34" />
      <path d="M4 6h.01" />
      <path d="M2.29 9.62A10 10 0 1 0 21.31 8.35" />
      <path d="M16.24 7.76A6 6 0 1 0 8.23 16.67" />
      <path d="M12 18h.01" />
      <path d="M17.99 11.66A6 6 0 0 1 15.77 16.67" />
      <circle cx="12" cy="12" r="2" />
      <path d="M13.41 10.59l5.66-5.66" />
    </svg>
  );
}

export function IconCash(p: IconBase) {
  return (
    <svg {...baseProps} {...p}>
      <rect x="2" y="6" width="20" height="12" rx="2" />
      <circle cx="12" cy="12" r="3" />
      <path d="M6 12h.01M18 12h.01" />
    </svg>
  );
}

export function IconHeadset(p: IconBase) {
  return (
    <svg {...baseProps} {...p}>
      <path d="M4 14v-2a8 8 0 0 1 16 0v2" />
      <path d="M18 14h2a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2h-2v-6z" />
      <path d="M6 14H4a2 2 0 0 0-2 2v2a2 2 0 0 0 2 2h2v-6z" />
    </svg>
  );
}

export function IconRocket(p: IconBase) {
  return (
    <svg {...baseProps} {...p}>
      <path d="M4 13a8 8 0 0 1 7-7 18 18 0 0 1 7 7l-3 3-7-7-3 3z" />
      <path d="M12 18l-4-4" />
      <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z" />
    </svg>
  );
}

export function IconChartBar(p: IconBase) {
  return (
    <svg {...baseProps} {...p}>
      <path d="M3 20h18" />
      <rect x="5" y="10" width="3" height="10" />
      <rect x="10.5" y="6" width="3" height="14" />
      <rect x="16" y="14" width="3" height="6" />
    </svg>
  );
}

export function IconSettings(p: IconBase) {
  return (
    <svg {...baseProps} {...p}>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9c.36.16.66.42.88.74H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  );
}

export function IconPlus(p: IconBase) {
  return (
    <svg {...baseProps} {...p}>
      <path d="M12 5v14M5 12h14" />
    </svg>
  );
}

export function IconChevronRight(p: IconBase) {
  return (
    <svg {...baseProps} {...p}>
      <path d="M9 18l6-6-6-6" />
    </svg>
  );
}

export function IconArrowRight(p: IconBase) {
  return (
    <svg {...baseProps} {...p}>
      <path d="M5 12h14M12 5l7 7-7 7" />
    </svg>
  );
}

export function IconRobot(p: IconBase) {
  return (
    <svg {...baseProps} {...p}>
      <rect x="3" y="8" width="18" height="12" rx="2" />
      <path d="M12 4v4M8 8V6M16 8V6" />
      <circle cx="9" cy="14" r="1" />
      <circle cx="15" cy="14" r="1" />
    </svg>
  );
}

export function IconBell(p: IconBase) {
  return (
    <svg {...baseProps} {...p}>
      <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
      <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
    </svg>
  );
}

export function IconSearch(p: IconBase) {
  return (
    <svg {...baseProps} {...p}>
      <circle cx="11" cy="11" r="8" />
      <path d="M21 21l-4.35-4.35" />
    </svg>
  );
}

export function IconEye(p: IconBase) {
  return (
    <svg {...baseProps} {...p}>
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

export function IconBolt(p: IconBase) {
  return (
    <svg {...baseProps} {...p} fill="currentColor" stroke="none">
      <path d="M13 2L3 14h7l-1 8 10-12h-7l1-8z" />
    </svg>
  );
}

export function IconCheck(p: IconBase) {
  return (
    <svg {...baseProps} {...p}>
      <path d="M5 12l5 5L20 7" />
    </svg>
  );
}

export function IconWorld(p: IconBase) {
  return (
    <svg {...baseProps} {...p}>
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" />
    </svg>
  );
}

export function IconId(p: IconBase) {
  return (
    <svg {...baseProps} {...p}>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <circle cx="9" cy="11" r="2" />
      <path d="M14 9h4M14 13h4M5 17h6" />
    </svg>
  );
}

export function IconInstagram(p: IconBase) {
  return (
    <svg {...baseProps} {...p}>
      <rect x="2" y="2" width="20" height="20" rx="5" />
      <circle cx="12" cy="12" r="4" />
      <circle cx="17.5" cy="6.5" r="1" fill="currentColor" />
    </svg>
  );
}

export function IconFacebook(p: IconBase) {
  return (
    <svg {...baseProps} {...p}>
      <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z" />
    </svg>
  );
}

export function IconLinkedin(p: IconBase) {
  return (
    <svg {...baseProps} {...p}>
      <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-4 0v7h-4v-7a6 6 0 0 1 6-6z" />
      <rect x="2" y="9" width="4" height="12" />
      <circle cx="4" cy="4" r="2" />
    </svg>
  );
}

export function IconMail(p: IconBase) {
  return (
    <svg {...baseProps} {...p}>
      <rect x="2" y="4" width="20" height="16" rx="2" />
      <path d="M2 7l10 7 10-7" />
    </svg>
  );
}

export function IconPhone(p: IconBase) {
  return (
    <svg {...baseProps} {...p}>
      <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.37 1.9.72 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.35 1.85.59 2.81.72A2 2 0 0 1 22 16.92z" />
    </svg>
  );
}

export function IconWhatsApp(p: IconBase) {
  return (
    <svg {...baseProps} {...p}>
      <path d="M3 21l1.65-3.8a9 9 0 1 1 3.4 2.9L3 21z" />
      <path d="M9 10c.5 2 1.5 3 3.5 4 1 .5 2 0 2.5-.5" />
    </svg>
  );
}

export function IconBuildingStore(p: IconBase) {
  return (
    <svg {...baseProps} {...p}>
      <path d="M3 21V10l9-6 9 6v11" />
      <path d="M3 10h18" />
      <path d="M9 21V14h6v7" />
    </svg>
  );
}

export function IconBuildingHospital(p: IconBase) {
  return (
    <svg {...baseProps} {...p}>
      <path d="M3 21V7l9-4 9 4v14" />
      <path d="M12 9v6M9 12h6" />
    </svg>
  );
}

export function IconCode(p: IconBase) {
  return (
    <svg {...baseProps} {...p}>
      <path d="M16 18l6-6-6-6M8 6l-6 6 6 6" />
    </svg>
  );
}

export function IconTruck(p: IconBase) {
  return (
    <svg {...baseProps} {...p}>
      <path d="M1 3h15v13H1z" />
      <path d="M16 8h4l3 3v5h-7V8z" />
      <circle cx="5.5" cy="18.5" r="2.5" />
      <circle cx="18.5" cy="18.5" r="2.5" />
    </svg>
  );
}

export function IconAlertCircle(p: IconBase) {
  return (
    <svg {...baseProps} {...p}>
      <circle cx="12" cy="12" r="10" />
      <path d="M12 8v4M12 16h.01" />
    </svg>
  );
}

export function IconLoader(p: IconBase) {
  return (
    <svg {...baseProps} {...p} style={{ animation: 'spin 1s linear infinite' }}>
      <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
    </svg>
  );
}

export function IconX(p: IconBase) {
  return (
    <svg {...baseProps} {...p}>
      <path d="M18 6L6 18M6 6l12 12" />
    </svg>
  );
}

export function IconInbox(p: IconBase) {
  return (
    <svg {...baseProps} {...p}>
      <path d="M22 12h-6l-2 3h-4l-2-3H2" />
      <path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" />
    </svg>
  );
}


export const ICONS_BY_NAME: Record<string, (p: IconBase) => JSX.Element> = {
  'ti-radar': IconRadar,
  'ti-cash': IconCash,
  'ti-headset': IconHeadset,
  'ti-rocket': IconRocket,
  'ti-chart-bar': IconChartBar,
  'ti-settings': IconSettings,
  'ti-robot': IconRobot,
};

export function IconFromName({ name, ...props }: { name: string } & IconBase) {
  const Icon = ICONS_BY_NAME[name] ?? IconRobot;
  return <Icon {...props} />;
}
