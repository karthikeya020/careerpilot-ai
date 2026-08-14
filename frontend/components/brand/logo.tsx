/**
 * The CareerPilot mark: an open progress ring with a bright leading node --
 * literally an abbreviated version of the Career Twin readiness ring
 * elsewhere in the product (see app/career-twin/page.tsx), doubling as a
 * "C" letterform. Deliberately simple and geometric so it holds up at
 * favicon size and reads the same everywhere it appears.
 *
 * variant="badge": self-contained rounded-square gradient badge (default;
 * use standalone -- header, favicon, marketing surfaces).
 * variant="mark": transparent, drawn in currentColor only -- drop inside an
 * existing colored container (e.g. the auth sidebar's translucent square).
 */
export function Logo({
  size = 32,
  variant = "badge",
  className,
}: {
  size?: number;
  variant?: "badge" | "mark";
  className?: string;
}) {
  const strokeColor = variant === "badge" ? "white" : "currentColor";
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" className={className} aria-hidden="true">
      {variant === "badge" && (
        <>
          <defs>
            <linearGradient id="logo-badge-grad" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="var(--color-brand)" />
              <stop offset="100%" stopColor="var(--color-brand-2)" />
            </linearGradient>
          </defs>
          <rect width="40" height="40" rx="10" fill="url(#logo-badge-grad)" />
        </>
      )}
      <circle
        cx="20"
        cy="20"
        r="11"
        fill="none"
        stroke={strokeColor}
        strokeWidth="4.5"
        strokeLinecap="round"
        strokeDasharray="54.7 69.115"
        transform="rotate(-12.5 20 20)"
      />
      <circle cx="30.74" cy="17.62" r="3.4" fill={strokeColor} />
    </svg>
  );
}
