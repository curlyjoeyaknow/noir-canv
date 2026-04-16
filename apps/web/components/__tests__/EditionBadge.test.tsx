import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { EditionBadge } from "@/components/gallery/EditionBadge";

describe("EditionBadge", () => {
  it("shows 'Sold Out' when editionsSold >= editionSize", () => {
    render(<EditionBadge editionsSold={15} editionSize={15} />);
    expect(screen.getByText("Sold Out")).toBeInTheDocument();
    expect(screen.queryByText("Almost Gone")).not.toBeInTheDocument();
  });

  it("shows 'Sold Out' when editionsSold exceeds editionSize", () => {
    render(<EditionBadge editionsSold={20} editionSize={15} />);
    expect(screen.getByText("Sold Out")).toBeInTheDocument();
  });

  it("shows 'Almost Gone' when remaining <= 2 and not sold out", () => {
    render(<EditionBadge editionsSold={13} editionSize={15} />);
    expect(screen.getByText("Almost Gone")).toBeInTheDocument();
    expect(screen.queryByText("Sold Out")).not.toBeInTheDocument();
  });

  it("shows 'Almost Gone' when exactly 1 remaining", () => {
    render(<EditionBadge editionsSold={14} editionSize={15} />);
    expect(screen.getByText("Almost Gone")).toBeInTheDocument();
  });

  it("shows neither badge when plenty remaining", () => {
    render(<EditionBadge editionsSold={5} editionSize={15} />);
    expect(screen.queryByText("Sold Out")).not.toBeInTheDocument();
    expect(screen.queryByText("Almost Gone")).not.toBeInTheDocument();
  });

  it("displays sold count text", () => {
    render(<EditionBadge editionsSold={8} editionSize={15} />);
    expect(screen.getByText("8 of 15 sold")).toBeInTheDocument();
  });

  it("formats large numbers with locale separator", () => {
    render(<EditionBadge editionsSold={1200} editionSize={2000} />);
    expect(screen.getByText("1,200 of 2,000 sold")).toBeInTheDocument();
  });

  it("renders a progress bar with correct aria attributes", () => {
    render(<EditionBadge editionsSold={8} editionSize={15} />);
    const progressBar = screen.getByRole("progressbar");
    expect(progressBar).toHaveAttribute("aria-valuenow", "8");
    expect(progressBar).toHaveAttribute("aria-valuemin", "0");
    expect(progressBar).toHaveAttribute("aria-valuemax", "15");
    expect(progressBar).toHaveAttribute(
      "aria-label",
      "8 of 15 editions sold",
    );
  });

  it("sets progress bar width proportionally", () => {
    const { container } = render(
      <EditionBadge editionsSold={10} editionSize={20} />,
    );
    const progressFill = container.querySelector("[role='progressbar'] > div");
    expect(progressFill).toHaveStyle({ width: "50%" });
  });

  it("caps progress bar width at 100% when oversold", () => {
    const { container } = render(
      <EditionBadge editionsSold={25} editionSize={15} />,
    );
    const progressFill = container.querySelector("[role='progressbar'] > div");
    expect(progressFill).toHaveStyle({ width: "100%" });
  });
});
