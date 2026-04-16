"use client";

import { useEffect } from "react";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function ArtistsError({ error, reset }: ErrorProps) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="flex min-h-[60vh] flex-col items-center justify-center gap-6 px-4">
      <h1 className="font-serif text-3xl text-foreground">Something went wrong</h1>
      <p className="text-muted">We couldn&apos;t load this artist profile. Please try again.</p>
      <button
        onClick={reset}
        className="rounded-sm border border-border px-6 py-2 text-sm text-foreground transition-colors hover:border-accent hover:text-accent"
      >
        Try again
      </button>
    </main>
  );
}
