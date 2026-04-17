"use client";

import { useRouter } from "next/navigation";

interface BuyButtonProps {
  pieceSlug: string;
  disabled?: boolean;
}

export function BuyButton({ pieceSlug, disabled = false }: BuyButtonProps) {
  const router = useRouter();

  if (disabled) {
    return (
      <button
        disabled
        aria-disabled="true"
        className="mt-6 w-full cursor-not-allowed rounded-sm border border-border bg-surface px-6 py-4 text-sm font-semibold uppercase tracking-widest text-dim opacity-50"
      >
        Sold Out
      </button>
    );
  }

  return (
    <button
      onClick={() => router.push(`/checkout?piece=${pieceSlug}`)}
      className="mt-6 w-full rounded-sm border border-accent bg-accent px-6 py-4 text-sm font-semibold uppercase tracking-widest text-background transition-all duration-200 hover:bg-accent-hover hover:border-accent-hover focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 focus:ring-offset-background"
    >
      Buy Now
    </button>
  );
}
