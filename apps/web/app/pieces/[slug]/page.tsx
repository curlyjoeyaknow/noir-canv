import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";

import { getPieces, getPiece, getArtistName, getMockupsForPiece } from "@/lib/data";
import { formatPrice } from "@/lib/schemas";
import { MockupViewer } from "@/components/gallery/MockupViewer";
import { EditionBadge } from "@/components/gallery/EditionBadge";
import { BuyButton } from "@/components/gallery/BuyButton";

interface PageProps {
  params: Promise<{ slug: string }>;
}

export function generateStaticParams() {
  return getPieces().map((p) => ({ slug: p.slug }));
}

export async function generateMetadata({
  params,
}: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const piece = getPiece(slug);
  if (!piece) return {};
  return {
    title: piece.title,
    description: piece.description.slice(0, 160),
  };
}

export default async function PieceDetailPage({ params }: PageProps) {
  const { slug } = await params;
  const piece = getPiece(slug);
  if (!piece) notFound();

  const artistName = getArtistName(piece.artistSlug);
  const isSoldOut = piece.editionsSold >= piece.editionSize;
  const mockups = getMockupsForPiece(slug);

  return (
    <article className="mx-auto max-w-7xl px-6 py-16 md:px-8 md:py-20">
      <div className="flex flex-col gap-12 lg:flex-row lg:gap-16">
        {/* Image & Mockups */}
        <div className="w-full space-y-6 lg:max-w-xl">
          <div className="relative aspect-[3/4] w-full overflow-hidden rounded-sm bg-card shadow-xl shadow-black/20">
            <Image
              src={piece.imageUrl}
              alt={piece.title}
              fill
              sizes="(max-width: 1024px) 100vw, 576px"
              className="object-cover"
              priority
            />
          </div>
          {mockups.length > 0 && (
            <MockupViewer
              pieceTitle={piece.title}
              mockups={mockups.map((m) => ({
                type: m.type,
                variant: m.variant,
                imageUrl: m.imageUrl,
              }))}
            />
          )}
        </div>

        {/* Details */}
        <div className="flex flex-1 flex-col">
          <Link
            href={`/artists/${piece.artistSlug}`}
            className="text-sm font-medium text-accent transition-colors duration-200 hover:text-accent-hover"
          >
            {artistName}
          </Link>

          <h1 className="mt-2 font-serif text-3xl font-bold tracking-tight text-foreground md:text-4xl">
            {piece.title}
          </h1>

          <p className="mt-6 leading-relaxed text-muted">
            {piece.description}
          </p>

          {/* Metadata */}
          <dl className="mt-8 grid grid-cols-1 gap-3 text-sm sm:grid-cols-2 lg:grid-cols-3">
            {piece.medium && (
              <div className="rounded-sm border border-border/60 bg-surface/50 p-3">
                <dt className="text-xs font-semibold uppercase tracking-wider text-dim">Medium</dt>
                <dd className="mt-1.5 text-foreground">{piece.medium}</dd>
              </div>
            )}
            {piece.dimensions && (
              <div className="rounded-sm border border-border/60 bg-surface/50 p-3">
                <dt className="text-xs font-semibold uppercase tracking-wider text-dim">Dimensions</dt>
                <dd className="mt-1.5 text-foreground">{piece.dimensions}</dd>
              </div>
            )}
            {piece.year && (
              <div className="rounded-sm border border-border/60 bg-surface/50 p-3">
                <dt className="text-xs font-semibold uppercase tracking-wider text-dim">Year</dt>
                <dd className="mt-1.5 text-foreground">{piece.year}</dd>
              </div>
            )}
          </dl>

          {/* Price & Edition */}
          <div className="mt-8 border-t border-border/80 pt-8">
            {isSoldOut ? (
              <p className="text-lg font-semibold text-sold-out">Sold Out</p>
            ) : (
              <p className="font-serif text-3xl font-semibold text-foreground">
                {formatPrice(piece.priceCents, piece.currency)}
              </p>
            )}

            <EditionBadge
              editionsSold={piece.editionsSold}
              editionSize={piece.editionSize}
              className="mt-5"
            />

            <BuyButton pieceSlug={piece.slug} disabled={isSoldOut} />
          </div>

          {/* Tags */}
          {piece.tags.length > 0 && (
            <div className="mt-8 flex flex-wrap gap-2">
              {piece.tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-sm border border-border bg-surface px-3 py-1.5 text-xs text-muted transition-colors duration-200 hover:border-border-hover hover:text-foreground"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="mt-14">
        <Link
          href={`/artists/${piece.artistSlug}`}
          className="text-sm text-muted transition-colors duration-200 hover:text-accent"
        >
          &larr; More by {artistName}
        </Link>
      </div>
    </article>
  );
}
