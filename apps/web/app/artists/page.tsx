import type { Metadata } from "next";

import { getArtists } from "@/lib/data";
import { ArtistCard } from "@/components/ArtistCard";

export const metadata: Metadata = {
  title: "Our Artists",
  description:
    "Meet the independent artists behind Noir Canvas. Each brings a distinct style and vision to our limited edition collection.",
};

export default function ArtistsPage() {
  const artists = getArtists();

  return (
    <section className="mx-auto max-w-7xl px-6 py-16 md:px-8 md:py-20">
      <h1 className="font-serif text-3xl font-bold tracking-tight text-foreground md:text-4xl">
        Our Artists
      </h1>
      <p className="mt-4 max-w-2xl leading-relaxed text-muted">
        Each artist brings a unique perspective and style to our curated
        collection of limited edition works.
      </p>
      <div className="artist-grid mt-14">
        {artists.map((artist) => (
          <ArtistCard key={artist.slug} artist={artist} />
        ))}
      </div>
    </section>
  );
}
