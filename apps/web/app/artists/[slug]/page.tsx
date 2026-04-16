import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";

import { getArtists, getArtist, getArtistPieces } from "@/lib/data";
import { PieceCard } from "@/components/PieceCard";
import { ImageCarousel } from "@/components/gallery/ImageCarousel";

interface PageProps {
  params: Promise<{ slug: string }>;
}

export function generateStaticParams() {
  return getArtists().map((a) => ({ slug: a.slug }));
}

export async function generateMetadata({
  params,
}: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const artist = getArtist(slug);
  if (!artist) return {};
  return {
    title: artist.name,
    description: artist.bio.slice(0, 160),
  };
}

export default async function ArtistDetailPage({ params }: PageProps) {
  const { slug } = await params;
  const artist = getArtist(slug);
  if (!artist) notFound();

  const pieces = getArtistPieces(slug);

  return (
    <article className="mx-auto max-w-7xl px-6 py-16 md:px-8 md:py-20">
      {/* Hero */}
      <section className="flex flex-col items-center gap-8 sm:flex-row sm:items-start sm:gap-12">
        <div className="relative h-56 w-56 shrink-0 overflow-hidden rounded-full border border-border/80 bg-card shadow-lg shadow-black/30 md:h-64 md:w-64">
          <Image
            src={artist.portraitUrl}
            alt={`Portrait of ${artist.name}`}
            fill
            sizes="(max-width: 768px) 224px, 256px"
            className="object-cover"
            priority
          />
        </div>

        <div className="text-center sm:text-left">
          <h1 className="font-serif text-3xl font-bold tracking-tight text-foreground md:text-4xl">
            {artist.name}
          </h1>
          <p className="mt-2 text-lg font-medium text-accent">{artist.style.medium}</p>
          <p className="mt-6 max-w-2xl leading-relaxed text-muted">
            {artist.bio}
          </p>
        </div>
      </section>

      {/* Artist Statement */}
      <section className="mt-16 border-l-2 border-accent/80 pl-6">
        <blockquote className="max-w-3xl font-serif text-lg italic leading-relaxed text-foreground/90">
          &ldquo;{artist.artistStatement}&rdquo;
        </blockquote>
      </section>

      {/* Style */}
      <section className="mt-14">
        <h2 className="font-serif text-2xl font-semibold text-foreground">
          Style
        </h2>
        <dl className="mt-5 grid grid-cols-1 gap-4 text-sm sm:grid-cols-3">
          <div className="rounded-sm border border-border/60 bg-surface/50 p-4">
            <dt className="text-xs font-semibold uppercase tracking-wider text-dim">Medium</dt>
            <dd className="mt-1.5 text-foreground">{artist.style.medium}</dd>
          </div>
          <div className="rounded-sm border border-border/60 bg-surface/50 p-4">
            <dt className="text-xs font-semibold uppercase tracking-wider text-dim">Palette</dt>
            <dd className="mt-1.5 text-foreground">{artist.style.palette}</dd>
          </div>
          <div className="rounded-sm border border-border/60 bg-surface/50 p-4">
            <dt className="text-xs font-semibold uppercase tracking-wider text-dim">Subjects</dt>
            <dd className="mt-1.5 text-foreground">{artist.style.subjects}</dd>
          </div>
        </dl>
      </section>

      {/* Influences */}
      <section className="mt-14">
        <h2 className="font-serif text-2xl font-semibold text-foreground">
          Influences
        </h2>
        <div className="mt-4 flex flex-wrap gap-2">
          {artist.influences.map((influence) => (
            <span
              key={influence}
              className="rounded-sm border border-border bg-surface px-3 py-1.5 text-sm text-muted transition-colors duration-200 hover:border-border-hover hover:text-foreground"
            >
              {influence}
            </span>
          ))}
        </div>
      </section>

      {/* Featured Works Carousel */}
      {pieces.length > 1 && (
        <section className="mt-20">
          <h2 className="font-serif text-2xl font-semibold text-foreground md:text-3xl">
            Featured Works
          </h2>
          <div className="mx-auto mt-10 max-w-xl">
            <ImageCarousel
              images={pieces.map((p) => ({
                src: p.imageUrl,
                alt: p.title,
              }))}
            />
          </div>
        </section>
      )}

      {/* All Pieces */}
      {pieces.length > 0 && (
        <section className="mt-20">
          <h2 className="font-serif text-2xl font-semibold text-foreground md:text-3xl">
            Works by {artist.name}
          </h2>
          <div className="gallery-grid mt-10">
            {pieces.map((piece, i) => (
              <PieceCard
                key={piece.slug}
                piece={piece}
                artistName={artist.name}
                priority={i < 3}
              />
            ))}
          </div>
        </section>
      )}

      <div className="mt-14">
        <Link
          href="/artists"
          className="text-sm text-muted transition-colors duration-200 hover:text-accent"
        >
          &larr; All Artists
        </Link>
      </div>
    </article>
  );
}
