"use client";

import { useMemo, useState } from "react";

import { PieceCard } from "@/components/PieceCard";
import type { Artist, Piece } from "@/lib/schemas";

interface PieceBrowserProps {
  pieces: Piece[];
  artists: Artist[];
}

type SortKey = "newest" | "oldest" | "artist" | "price-asc" | "price-desc";

const SORT_OPTIONS: { value: SortKey; label: string }[] = [
  { value: "newest", label: "Newest" },
  { value: "oldest", label: "Oldest" },
  { value: "artist", label: "Artist A–Z" },
  { value: "price-asc", label: "Price: Low to High" },
  { value: "price-desc", label: "Price: High to Low" },
];

export function PieceBrowser({ pieces, artists }: PieceBrowserProps) {
  const [filterArtist, setFilterArtist] = useState<string>("all");
  const [sortBy, setSortBy] = useState<SortKey>("newest");

  const artistMap = useMemo(
    () => Object.fromEntries(artists.map((a) => [a.slug, a.name])),
    [artists],
  );

  const filtered = useMemo(() => {
    let result = filterArtist === "all"
      ? [...pieces]
      : pieces.filter((p) => p.artistSlug === filterArtist);

    switch (sortBy) {
      case "newest":
        result = result.slice().reverse();
        break;
      case "oldest":
        break;
      case "artist":
        result = result.slice().sort((a, b) =>
          (artistMap[a.artistSlug] ?? a.artistSlug).localeCompare(
            artistMap[b.artistSlug] ?? b.artistSlug,
          ),
        );
        break;
      case "price-asc":
        result = result.slice().sort((a, b) => a.priceCents - b.priceCents);
        break;
      case "price-desc":
        result = result.slice().sort((a, b) => b.priceCents - a.priceCents);
        break;
    }

    return result;
  }, [pieces, filterArtist, sortBy, artistMap]);

  return (
    <div>
      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3 border-b border-border/60 pb-6">
        {/* Artist filter */}
        <div className="flex items-center gap-2">
          <label
            htmlFor="filter-artist"
            className="text-xs font-semibold uppercase tracking-wider text-dim"
          >
            Artist
          </label>
          <select
            id="filter-artist"
            value={filterArtist}
            onChange={(e) => setFilterArtist(e.target.value)}
            className="min-h-[44px] rounded-sm border border-border bg-surface px-3 py-2 text-sm text-foreground transition-colors focus:border-accent focus:outline-none"
          >
            <option value="all">All Artists</option>
            {artists
              .slice()
              .sort((a, b) => a.name.localeCompare(b.name))
              .map((a) => (
                <option key={a.slug} value={a.slug}>
                  {a.name}
                </option>
              ))}
          </select>
        </div>

        {/* Sort */}
        <div className="flex items-center gap-2">
          <label
            htmlFor="sort-by"
            className="text-xs font-semibold uppercase tracking-wider text-dim"
          >
            Sort
          </label>
          <select
            id="sort-by"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortKey)}
            className="min-h-[44px] rounded-sm border border-border bg-surface px-3 py-2 text-sm text-foreground transition-colors focus:border-accent focus:outline-none"
          >
            {SORT_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>

        {/* Count */}
        <p className="ml-auto text-sm text-dim">
          {filtered.length} {filtered.length === 1 ? "work" : "works"}
        </p>
      </div>

      {/* Grid */}
      {filtered.length === 0 ? (
        <div className="flex min-h-[40vh] items-center justify-center">
          <p className="text-muted">No works found for this selection.</p>
        </div>
      ) : (
        <div className="gallery-grid mt-10">
          {filtered.map((piece, i) => (
            <PieceCard
              key={piece.slug}
              piece={piece}
              artistName={artistMap[piece.artistSlug] ?? piece.artistSlug}
              priority={i < 6}
            />
          ))}
        </div>
      )}
    </div>
  );
}
