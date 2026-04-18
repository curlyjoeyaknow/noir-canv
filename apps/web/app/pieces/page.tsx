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
    <main className="mx-auto max-w-7xl px-6 py-12 md:px-8 md:py-16">
      <h1 className="font-serif text-3xl font-bold tracking-tight text-foreground md:text-4xl">
        All Works
      </h1>

      <div className="mt-8">
        <PieceBrowser pieces={pieces} artists={artists} />
      </div>
    </main>
  );
}
