import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";

import {
  getCollections,
  getCollection,
  getCollectionPieces,
  getArtistName,
} from "@/lib/data";
import { PieceCard } from "@/components/PieceCard";

interface PageProps {
  params: Promise<{ slug: string }>;
}

export function generateStaticParams() {
  return getCollections().map((c) => ({ slug: c.slug }));
}

export async function generateMetadata({
  params,
}: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const collection = getCollection(slug);
  if (!collection) return {};
  return {
    title: collection.name,
    description: collection.description.slice(0, 160),
  };
}

export default async function CollectionDetailPage({ params }: PageProps) {
  const { slug } = await params;
  const collection = getCollection(slug);
  if (!collection) notFound();

  const pieces = getCollectionPieces(slug);

  return (
    <article className="mx-auto max-w-7xl px-6 py-16 md:px-8 md:py-20">
      {/* Hero */}
      <section className="relative aspect-[16/9] overflow-hidden rounded-sm bg-card shadow-xl shadow-black/20 md:aspect-[21/9]">
        <Image
          src={collection.coverImageUrl}
          alt={collection.name}
          fill
          sizes="100vw"
          className="object-cover"
          priority
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent" />
        <div className="absolute bottom-0 p-6 md:p-10">
          <h1 className="font-serif text-2xl font-bold text-white sm:text-3xl md:text-4xl">
            {collection.name}
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-white/80 sm:text-base">
            {collection.description}
          </p>
        </div>
      </section>

      {/* Pieces grid */}
      {pieces.length > 0 && (
        <section className="mt-14">
          <h2 className="font-serif text-2xl font-semibold text-foreground md:text-3xl">
            {pieces.length} {pieces.length === 1 ? "Piece" : "Pieces"}
          </h2>
          <div className="gallery-grid mt-10">
            {pieces.map((piece, i) => (
              <PieceCard
                key={piece.slug}
                piece={piece}
                artistName={getArtistName(piece.artistSlug)}
                priority={i < 3}
              />
            ))}
          </div>
        </section>
      )}

      <div className="mt-14">
        <Link
          href="/collections"
          className="text-sm text-muted transition-colors duration-200 hover:text-accent"
        >
          &larr; All Collections
        </Link>
      </div>
    </article>
  );
}
