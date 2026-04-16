"use client";

interface EditionBadgeProps {
  editionsSold: number;
  editionSize: number;
  className?: string;
}

const fmt = new Intl.NumberFormat("en-US");

export function EditionBadge({
  editionsSold,
  editionSize,
  className,
}: EditionBadgeProps) {
  const isSoldOut = editionsSold >= editionSize;
  const remaining = editionSize - editionsSold;
  const isAlmostGone = !isSoldOut && remaining <= 2;
  const progress = Math.min((editionsSold / editionSize) * 100, 100);

  return (
    <div className={className}>
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted">
          {fmt.format(editionsSold)} of {fmt.format(editionSize)} sold
        </span>
        {isSoldOut && (
          <span className="font-semibold text-sold-out">Sold Out</span>
        )}
        {isAlmostGone && (
          <span className="font-semibold text-edition-gold">Almost Gone</span>
        )}
      </div>
      <div
        role="progressbar"
        aria-valuenow={editionsSold}
        aria-valuemin={0}
        aria-valuemax={editionSize}
        aria-label={`${fmt.format(editionsSold)} of ${fmt.format(editionSize)} editions sold`}
        className="mt-2 h-1.5 overflow-hidden rounded-full bg-surface"
      >
        <div
          className={`animate-progress h-full rounded-full ${
            isSoldOut
              ? "bg-sold-out"
              : isAlmostGone
                ? "bg-edition-gold"
                : "bg-accent"
          }`}
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
