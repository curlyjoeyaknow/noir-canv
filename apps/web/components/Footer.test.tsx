import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Footer } from "./Footer";

describe("Footer", () => {
  it("renders copyright text with the current year", () => {
    render(<Footer />);
    const year = new Date().getFullYear().toString();
    expect(
      screen.getByText(new RegExp(`© ${year} Noir Canvas`)),
    ).toBeInTheDocument();
  });

  it("contains gallery navigation links", () => {
    render(<Footer />);
    expect(screen.getByRole("link", { name: "Artists" })).toHaveAttribute(
      "href",
      "/artists",
    );
    expect(
      screen.getByRole("link", { name: "Collections" }),
    ).toHaveAttribute("href", "/collections");
  });

  it("contains social media links that open in new tabs", () => {
    render(<Footer />);
    const instagram = screen.getByRole("link", { name: "Instagram" });
    expect(instagram).toHaveAttribute("target", "_blank");
    expect(instagram).toHaveAttribute("rel", "noopener noreferrer");

    const twitter = screen.getByRole("link", { name: "X / Twitter" });
    expect(twitter).toHaveAttribute("target", "_blank");
    expect(twitter).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("renders the brand name 'Noir Canvas'", () => {
    render(<Footer />);
    expect(screen.getByText("Noir Canvas")).toBeInTheDocument();
  });
});
