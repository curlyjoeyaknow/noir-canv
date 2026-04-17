import Image from "next/image";
import Link from "next/link";

import type { Piece } from "@/lib/schemas";
import { formatPrice } from "@/lib/schemas";

interface PieceCardProps {
  piece: Piece;
  artistName: string;
  priority?: boolean;
}

function getEditionLabel(sold: number, total: number): string | null {
  if (sold >= total) return "Sold Out";
  if (total - sold <= 2) return "Almost Gone";
  return null;
}

export function PieceCard({ piece, artistName, priority = false }: PieceCardProps) {
  const isSoldOut = piece.editionsSold >= piece.editionSize;
  const editionLabel = getEditionLabel(piece.editionsSold, piece.editionSize);

  return (
    <Link href={`/pieces/${piece.slug}`} className="group block">
      <article className="transition-transform duration-400 ease-out group-hover:-translate-y-1.5">

        {/* Framed artwork */}
        <div className="artwork-frame">
          <div className="artwork-mat">
            {/* Artwork image */}
            <div className="relative aspect-[3/4]">
              <Image
                src={piece.imageUrl}
                alt={piece.title}
                fill
                sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
                className="object-contain"
                priority={priority}
              />
            </div>

            {/* Gold seal on mat */}
            <div className="artwork-seal">NC</div>

            {/* Edition badge — top-right corner of mat */}
            {editionLabel && (
              <span
                className={`absolute right-2 top-2 z-10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-widest ${
                  isSoldOut
                    ? "bg-sold-out text-white"
                    : "bg-edition-gold text-[#0d0c0a]"
                }`}
              >
                {editionLabel}
              </span>
            )}
          </div>
        </div>

        {/* Metadata below frame */}
        <div className="mt-4 space-y-1 px-0.5">
          <h3 className="font-serif text-base text-foreground transition-colors duration-200 group-hover:text-accent leading-snug">
            {piece.title}
          </h3>
          <p className="text-xs text-muted tracking-wide">{artistName}</p>

          <div className="flex items-center justify-between pt-1">
            {!isSoldOut && (
              <p className="text-sm font-medium text-accent">
                {formatPrice(piece.priceCents, piece.currency)}
              </p>
            )}
            <p className="ml-auto text-xs text-dim">
              Ed.&nbsp;{piece.editionsSold}/{piece.editionSize}
            </p>
          </div>
        </div>

      </article>
    </Link>
  );
}
