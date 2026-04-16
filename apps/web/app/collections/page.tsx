import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";

import { getCollections } from "@/lib/data";

export const metadata: Metadata = {
  title: "Collections",
  description:
    "Browse curated collections of limited edition art from Noir Canvas. Each collection groups works by theme, mood, or moment.",
};

export default function CollectionsPage() {
  const collections = getCollections();

  return (
    <section className="mx-auto max-w-7xl px-6 py-16 md:px-8 md:py-20">
      <h1 className="font-serif text-3xl font-bold tracking-tight text-foreground md:text-4xl">
        Collections
      </h1>
      <p className="mt-4 max-w-2xl leading-relaxed text-muted">
        Curated groupings by theme, mood, and moment. Each collection brings
        together works that share a visual conversation.
      </p>

      <div className="gallery-grid mt-14">
        {collections.map((collection) => (
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
                  <h2 className="font-serif text-xl text-white">
                    {collection.name}
                  </h2>
                  <p className="mt-1 line-clamp-2 text-sm text-white/80">
                    {collection.description}
                  </p>
                  <p className="mt-2 text-xs text-white/70">
                    {collection.pieceSlugs.length}{" "}
                    {collection.pieceSlugs.length === 1 ? "piece" : "pieces"}
                  </p>
                </div>
              </div>
            </article>
          </Link>
        ))}
      </div>
    </section>
  );
}
