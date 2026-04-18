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
  { value: "newest", label: "Date, new to old" },
  { value: "oldest", label: "Date, old to new" },
  { value: "artist", label: "Alphabetically, A–Z" },
  { value: "price-asc", label: "Price, low to high" },
  { value: "price-desc", label: "Price, high to low" },
];

export function PieceBrowser({ pieces, artists }: PieceBrowserProps) {
  const [filterArtist, setFilterArtist] = useState<string>("all");
  const [sortBy, setSortBy] = useState<SortKey>("newest");

  const sortedArtists = useMemo(
    () => artists.slice().sort((a, b) => a.name.localeCompare(b.name)),
    [artists],
  );

  const artistMap = useMemo(
    () => Object.fromEntries(artists.map((a) => [a.slug, a.name])),
    [artists],
  );

  const filtered = useMemo(() => {
    let result =
      filterArtist === "all"
        ? [...pieces]
        : pieces.filter((p) => p.artistSlug === filterArtist);

    switch (sortBy) {
      case "newest":
        result = result.slice().reverse();
        break;
      case "oldest":
        break;
      case "artist":
        result = result
          .slice()
          .sort((a, b) =>
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
      {/* Toolbar row — count left, sort right */}
      <div className="flex items-center justify-between border-b border-border/50 pb-4">
        <p className="text-sm text-dim">
          {filtered.length}{" "}
          {filtered.length === 1 ? "result" : "results"}
        </p>

        <div className="flex items-center gap-2">
          <label
            htmlFor="sort-by"
            className="hidden text-xs font-semibold uppercase tracking-wider text-dim sm:block"
          >
            Sort by
          </label>
          <select
            id="sort-by"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortKey)}
            className="min-h-[36px] rounded-sm border border-border/60 bg-transparent px-3 py-1.5 text-sm text-foreground transition-colors focus:border-accent focus:outline-none"
          >
            {SORT_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Artist filter pills — horizontally scrollable */}
      <div className="mt-4 flex gap-2 overflow-x-auto pb-1">
        <button
          type="button"
          onClick={() => setFilterArtist("all")}
          className={`flex-none rounded-sm border px-3.5 py-1.5 text-xs font-semibold uppercase tracking-wider transition-all duration-200 ${
            filterArtist === "all"
              ? "border-foreground bg-foreground text-background"
              : "border-border/60 text-muted hover:border-border-hover hover:text-foreground"
          }`}
        >
          All
        </button>
        {sortedArtists.map((artist) => (
          <button
            key={artist.slug}
            type="button"
            onClick={() =>
              setFilterArtist(
                filterArtist === artist.slug ? "all" : artist.slug,
              )
            }
            className={`flex-none rounded-sm border px-3.5 py-1.5 text-xs font-semibold uppercase tracking-wider transition-all duration-200 ${
              filterArtist === artist.slug
                ? "border-foreground bg-foreground text-background"
                : "border-border/60 text-muted hover:border-border-hover hover:text-foreground"
            }`}
          >
            {artist.name}
          </button>
        ))}
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
              priority={i < 8}
            />
          ))}
        </div>
      )}
    </div>
  );
}
