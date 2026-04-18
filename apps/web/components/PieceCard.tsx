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
      <article>

        {/* Framed artwork — walnut frame with thin black inner liner */}
        <div className="artwork-frame">
          <div className="relative aspect-[2/3] overflow-hidden ring-[1.5px] ring-black/75">
            <Image
              src={piece.imageUrl}
              alt={piece.title}
              fill
              sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
              className="object-contain transition-transform duration-700 ease-out group-hover:scale-[1.02]"
              priority={priority}
            />
          </div>
        </div>

        {/* Metadata below frame */}
        <div className="mt-4 space-y-1 px-0.5">
          <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-dim">
            {artistName}
          </p>
          <h3 className="font-serif text-sm leading-snug text-foreground transition-colors duration-200 group-hover:text-accent">
            {piece.title}
          </h3>
          <div className="flex items-baseline justify-between pt-0.5">
            {isSoldOut ? (
              <span className="text-xs font-semibold text-sold-out">Sold Out</span>
            ) : (
              <span className="text-sm text-foreground">
                {formatPrice(piece.priceCents, piece.currency)}
              </span>
            )}
            <span
              className={`text-[10px] ${
                editionLabel && !isSoldOut
                  ? "font-semibold text-edition-gold"
                  : "text-dim"
              }`}
            >
              {editionLabel && !isSoldOut ? editionLabel : `Ed. ${piece.editionsSold}/${piece.editionSize}`}
            </span>
          </div>
        </div>

      </article>
    </Link>
  );
}
