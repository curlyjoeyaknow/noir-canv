import type { Metadata } from "next";

import { getArtists, getPieces } from "@/lib/data";
import { PieceBrowser } from "@/components/gallery/PieceBrowser";

export const metadata: Metadata = {
  title: "All Works",
  description: "Browse the complete Noir Canvas collection — original AI-generated fine art, filterable by artist and sortable by date, artist, or price.",
};

export default function PiecesPage() {
  const pieces = getPieces();
  const artists = getArtists();

  return (
    <main className="mx-auto max-w-7xl px-6 py-16 md:px-8 md:py-20">
      <header className="mb-10">
        <h1 className="font-serif text-4xl font-bold tracking-tight text-foreground md:text-5xl">
          All Works
        </h1>
        <p className="mt-4 max-w-2xl text-muted">
          The complete collection — {pieces.length} original works by {artists.length} artists.
        </p>
      </header>

      <PieceBrowser pieces={pieces} artists={artists} />
    </main>
  );
}
