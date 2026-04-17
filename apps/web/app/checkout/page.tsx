import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";

import { getPiece, getArtistName } from "@/lib/data";
import { CheckoutForm } from "@/components/gallery/CheckoutForm";

export const metadata: Metadata = {
  title: "Reserve Edition — Noir Canvas",
  description: "Reserve your limited edition artwork.",
};

interface PageProps {
  searchParams: Promise<{ piece?: string }>;
}

export default async function CheckoutPage({ searchParams }: PageProps) {
  const { piece: pieceSlug } = await searchParams;

  if (!pieceSlug) notFound();

  const piece = getPiece(pieceSlug);
  if (!piece) notFound();

  const isSoldOut = piece.editionsSold >= piece.editionSize;
  if (isSoldOut) notFound();

  const artistName = getArtistName(piece.artistSlug);

  return (
    <main className="mx-auto max-w-5xl px-6 py-16 md:px-8 md:py-20">
      <Link
        href={`/pieces/${piece.slug}`}
        className="text-sm text-muted transition-colors hover:text-accent"
      >
        &larr; Back to {piece.title}
      </Link>

      <h1 className="mt-6 font-serif text-3xl font-bold tracking-tight text-foreground md:text-4xl">
        Reserve Your Edition
      </h1>
      <p className="mt-2 text-muted">
        Limited editions — once sold, they&apos;re gone.
      </p>

      <div className="mt-10 grid gap-12 lg:grid-cols-2">
        {/* Piece preview */}
        <div className="space-y-4">
          <div className="relative aspect-[3/4] overflow-hidden rounded-sm bg-card shadow-lg shadow-black/20">
            <Image
              src={piece.imageUrl}
              alt={piece.title}
              fill
              sizes="(max-width: 1024px) 100vw, 480px"
              className="object-cover"
              priority
            />
          </div>
          <div className="space-y-1 text-sm text-muted">
            <p className="font-serif text-lg font-semibold text-foreground">
              {piece.title}
            </p>
            <p>by {artistName}</p>
            {piece.medium && <p>{piece.medium}</p>}
            {piece.dimensions && <p>{piece.dimensions}</p>}
            <p className="text-xs text-dim">
              Edition {piece.editionsSold + 1} of {piece.editionSize}
            </p>
          </div>
        </div>

        {/* Form */}
        <CheckoutForm piece={piece} artistName={artistName} />
      </div>
    </main>
  );
}
