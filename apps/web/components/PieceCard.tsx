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
      <article className="overflow-hidden rounded-sm border border-transparent transition-all duration-300 group-hover:border-border-hover group-hover:shadow-lg group-hover:shadow-black/20">
        <div className="relative aspect-[3/4] overflow-hidden bg-[#f4f2ef]">
          <div className="absolute inset-5 transition-transform duration-500 ease-out group-hover:scale-[1.03]">
            <Image
              src={piece.imageUrl}
              alt={piece.title}
              fill
              sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
              className="object-contain drop-shadow-md"
              priority={priority}
            />
          </div>
          {editionLabel && (
            <span
              className={`absolute right-3 top-3 z-10 rounded-sm px-2.5 py-1 text-xs font-semibold uppercase tracking-wider ${
                isSoldOut
                  ? "bg-sold-out text-white"
                  : "bg-edition-gold text-background"
              }`}
            >
              {editionLabel}
            </span>
          )}
        </div>

        <div className="space-y-1 px-3 pb-4 pt-4">
          <h3 className="font-serif text-lg text-foreground transition-colors duration-200 group-hover:text-accent">
            {piece.title}
          </h3>
          <p className="text-sm text-muted">{artistName}</p>

          <div className="flex items-center justify-between pt-1.5">
            {!isSoldOut && (
              <p className="text-sm font-medium text-foreground">
                {formatPrice(piece.priceCents, piece.currency)}
              </p>
            )}
            <p className="text-xs text-dim">
              Ed. {piece.editionsSold}/{piece.editionSize}
            </p>
          </div>
        </div>
      </article>
    </Link>
  );
}
