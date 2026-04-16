import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { Piece } from "@/lib/schemas";

import almostGoneFixture from "../__fixtures__/piece-almost-gone.json";
import soldOutFixture from "../__fixtures__/piece-sold-out.json";
import pieceFixture from "../__fixtures__/piece.json";
import { PieceCard } from "./PieceCard";

const piece = pieceFixture as Piece;
const soldOut = soldOutFixture as Piece;
const almostGone = almostGoneFixture as Piece;

describe("PieceCard", () => {
  it("renders the piece title", () => {
    render(<PieceCard piece={piece} artistName="Kai Voss" />);
    expect(screen.getByText("Dusk Amber II")).toBeInTheDocument();
  });

  it("shows the artist name", () => {
    render(<PieceCard piece={piece} artistName="Kai Voss" />);
    expect(screen.getByText("Kai Voss")).toBeInTheDocument();
  });

  it("shows the formatted price", () => {
    render(<PieceCard piece={piece} artistName="Kai Voss" />);
    expect(screen.getByText("$299")).toBeInTheDocument();
  });

  it("shows edition information", () => {
    render(<PieceCard piece={piece} artistName="Kai Voss" />);
    expect(screen.getByText("Ed. 8/15")).toBeInTheDocument();
  });

  it("links to the correct /pieces/[slug] URL", () => {
    render(<PieceCard piece={piece} artistName="Kai Voss" />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/pieces/kai-voss-001");
  });

  it('shows "Sold Out" when all editions are sold', () => {
    render(<PieceCard piece={soldOut} artistName="Kai Voss" />);
    expect(screen.getByText("Sold Out")).toBeInTheDocument();
  });

  it("hides the price when sold out", () => {
    render(<PieceCard piece={soldOut} artistName="Kai Voss" />);
    expect(screen.queryByText("$299")).not.toBeInTheDocument();
  });

  it('shows "Almost Gone" when nearly sold out', () => {
    render(<PieceCard piece={almostGone} artistName="Kai Voss" />);
    expect(screen.getByText("Almost Gone")).toBeInTheDocument();
  });

  it("does not show a badge when editions are plentiful", () => {
    const plentiful: Piece = { ...piece, editionsSold: 3 };
    render(<PieceCard piece={plentiful} artistName="Kai Voss" />);
    expect(screen.queryByText("Sold Out")).not.toBeInTheDocument();
    expect(screen.queryByText("Almost Gone")).not.toBeInTheDocument();
  });
});
