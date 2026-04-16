import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { Artist } from "@/lib/schemas";

import artistFixture from "../__fixtures__/artist.json";
import { ArtistCard } from "./ArtistCard";

const artist = artistFixture as Artist;

describe("ArtistCard", () => {
  it("renders the artist name", () => {
    render(<ArtistCard artist={artist} />);
    expect(screen.getByText("Kai Voss")).toBeInTheDocument();
  });

  it("links to the correct /artists/[slug] URL", () => {
    render(<ArtistCard artist={artist} />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/artists/kai-voss");
  });

  it("renders the artist portrait with a descriptive alt text", () => {
    render(<ArtistCard artist={artist} />);
    const img = screen.getByRole("img");
    expect(img).toHaveAttribute("alt", "Portrait of Kai Voss");
  });

  it("displays the artist's medium", () => {
    render(<ArtistCard artist={artist} />);
    expect(screen.getByText("Abstract minimalist")).toBeInTheDocument();
  });
});
