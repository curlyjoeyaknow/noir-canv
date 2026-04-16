import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { Header } from "./Header";

vi.mock("@/components/MobileNavToggle", () => ({
  MobileNavToggle: () => <div data-testid="mobile-nav-toggle" />,
}));

describe("Header", () => {
  it("renders the site title 'Noir Canvas'", () => {
    render(<Header />);
    expect(screen.getByText("Noir Canvas")).toBeInTheDocument();
  });

  it("renders navigation links for Home, Artists, and Collections", () => {
    render(<Header />);
    expect(screen.getByRole("link", { name: "Home" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Artists" })).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Collections" }),
    ).toBeInTheDocument();
  });

  it("links to correct hrefs", () => {
    render(<Header />);
    expect(screen.getByRole("link", { name: "Home" })).toHaveAttribute(
      "href",
      "/",
    );
    expect(screen.getByRole("link", { name: "Artists" })).toHaveAttribute(
      "href",
      "/artists",
    );
    expect(
      screen.getByRole("link", { name: "Collections" }),
    ).toHaveAttribute("href", "/collections");
  });

  it("renders the site title as a link to the homepage", () => {
    render(<Header />);
    const titleLink = screen.getByRole("link", { name: "Noir Canvas" });
    expect(titleLink).toHaveAttribute("href", "/");
  });
});
