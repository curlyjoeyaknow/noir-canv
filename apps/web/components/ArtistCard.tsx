import Image from "next/image";
import Link from "next/link";

import type { Artist } from "@/lib/schemas";

interface ArtistCardProps {
  artist: Artist;
}

export function ArtistCard({ artist }: ArtistCardProps) {
  return (
    <Link href={`/artists/${artist.slug}`} className="group block">
      <article className="flex flex-col items-center text-center transition-transform duration-300 ease-out group-hover:-translate-y-1">
        <div className="relative h-36 w-36 overflow-hidden rounded-full border border-border bg-card transition-all duration-300 sm:h-40 sm:w-40 group-hover:border-accent/40 group-hover:shadow-lg group-hover:shadow-accent/10">
          <Image
            src={artist.portraitUrl}
            alt={`Portrait of ${artist.name}`}
            fill
            sizes="(max-width: 640px) 144px, 160px"
            className="object-cover transition-transform duration-500 ease-out group-hover:scale-105"
          />
        </div>
        <h3 className="mt-4 font-serif text-xl text-foreground transition-colors duration-200 group-hover:text-accent">
          {artist.name}
        </h3>
        <p className="mt-1.5 text-sm text-muted">{artist.style.medium}</p>
      </article>
    </Link>
  );
}
