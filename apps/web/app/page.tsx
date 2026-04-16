import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";

import {
  getArtists,
  getPieces,
  getCollections,
  getArtistName,
} from "@/lib/data";
import { ArtistCard } from "@/components/ArtistCard";
import { PieceCard } from "@/components/PieceCard";

export const metadata: Metadata = {
  title: "Noir Canvas — Limited Edition Art",
  description:
    "Curated limited edition canvas art from independent artists. Each piece is numbered, authenticated, and crafted for modern spaces.",
};

export default function HomePage() {
  const artists = getArtists();
  const pieces = getPieces();
  const collections = getCollections();

  const featuredPieces = pieces
    .filter((p) => p.editionsSold < p.editionSize)
    .slice(0, 6);
  const featuredArtists = artists.slice(0, 3);
  const featuredCollections = collections.slice(0, 3);

  return (
    <>
      <section className="relative mx-auto max-w-7xl px-6 pb-20 pt-28 text-center md:px-8 md:pb-28 md:pt-40">
        <div className="animate-shimmer absolute inset-x-0 top-0 h-px" />
        <p className="animate-fade-in text-xs font-semibold uppercase tracking-[0.2em] text-accent">
          Limited Edition Art
        </p>
        <h1 className="animate-fade-in-slow mt-6 font-serif text-4xl font-bold tracking-tight text-foreground sm:text-5xl md:text-6xl lg:text-7xl">
          Noir Canvas
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-muted">
          Curated works from independent artists, each numbered and
          authenticated. Discover original pieces crafted for modern spaces.
        </p>
        <div className="mt-12 flex flex-col items-center justify-center gap-4 sm:flex-row">
          <Link
            href="/artists"
            className="rounded-sm bg-accent px-8 py-3.5 text-sm font-semibold tracking-wide text-background transition-all duration-300 hover:bg-accent-hover hover:shadow-lg hover:shadow-accent/20"
          >
            Discover Artists
          </Link>
          <Link
            href="/collections"
            className="rounded-sm border border-border px-8 py-3.5 text-sm font-semibold tracking-wide text-foreground transition-all duration-300 hover:border-accent hover:text-accent"
          >
            Browse Collections
          </Link>
        </div>
        <div className="animate-shimmer mx-auto mt-16 h-px max-w-xs" />
      </section>

      <section className="mx-auto max-w-7xl px-6 py-16 md:px-8 md:py-20">
        <div className="flex items-end justify-between">
          <h2 className="font-serif text-2xl font-semibold text-foreground md:text-3xl">
            Featured Works
          </h2>
          <Link
            href="/collections"
            className="inline-block py-2 text-sm text-muted transition-colors duration-200 hover:text-accent"
          >
            View all &rarr;
          </Link>
        </div>
        <div className="gallery-grid mt-10">
          {featuredPieces.map((piece, i) => (
            <PieceCard
              key={piece.slug}
              piece={piece}
              artistName={getArtistName(piece.artistSlug)}
              priority={i < 3}
            />
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-6 py-16 md:px-8 md:py-20">
        <div className="flex items-end justify-between">
          <h2 className="font-serif text-2xl font-semibold text-foreground md:text-3xl">
            Our Artists
          </h2>
          <Link
            href="/artists"
            className="inline-block py-2 text-sm text-muted transition-colors duration-200 hover:text-accent"
          >
            View all &rarr;
          </Link>
        </div>
        <div className="artist-grid mt-10">
          {featuredArtists.map((artist) => (
            <ArtistCard key={artist.slug} artist={artist} />
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-6 py-16 md:px-8 md:py-20">
        <div className="flex items-end justify-between">
          <h2 className="font-serif text-2xl font-semibold text-foreground md:text-3xl">
            Collections
          </h2>
          <Link
            href="/collections"
            className="inline-block py-2 text-sm text-muted transition-colors duration-200 hover:text-accent"
          >
            View all &rarr;
          </Link>
        </div>
        <div className="gallery-grid mt-10">
          {featuredCollections.map((collection) => (
            <Link
              key={collection.slug}
              href={`/collections/${collection.slug}`}
              className="group block overflow-hidden rounded-sm border border-transparent transition-all duration-300 hover:border-border-hover hover:shadow-lg hover:shadow-black/20"
            >
              <article>
                <div className="relative aspect-[4/3] overflow-hidden bg-card">
                  <Image
                    src={collection.coverImageUrl}
                    alt={collection.name}
                    fill
                    sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
                    className="object-cover transition-transform duration-500 ease-out group-hover:scale-105"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
                  <div className="absolute bottom-0 p-5">
                    <h3 className="font-serif text-xl text-white">
                      {collection.name}
                    </h3>
                    <p className="mt-1 line-clamp-2 text-sm text-white/80">
                      {collection.description}
                    </p>
                  </div>
                </div>
              </article>
            </Link>
          ))}
        </div>
      </section>
    </>
  );
}
