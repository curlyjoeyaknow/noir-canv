import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { MobileNavToggle } from "./MobileNavToggle";

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    onClick,
  }: {
    href: string;
    children: React.ReactNode;
    onClick?: () => void;
  }) => (
    <a href={href} onClick={onClick}>
      {children}
    </a>
  ),
}));

const links = [
  { href: "/gallery", label: "Gallery" },
  { href: "/artists", label: "Artists" },
  { href: "/collections", label: "Collections" },
];

describe("MobileNavToggle", () => {
  it("renders a toggle button with accessible aria-label", () => {
    render(<MobileNavToggle links={links} />);
    const button = screen.getByRole("button", { name: "Open menu" });
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute("aria-label", "Open menu");
  });

  it("button starts with aria-expanded false", () => {
    render(<MobileNavToggle links={links} />);
    expect(screen.getByRole("button")).toHaveAttribute("aria-expanded", "false");
  });

  it("clicking the button opens the mobile nav", () => {
    render(<MobileNavToggle links={links} />);
    fireEvent.click(screen.getByRole("button", { name: "Open menu" }));
    expect(
      screen.getByRole("navigation", { name: "Mobile navigation" }),
    ).toBeInTheDocument();
  });

  it("button aria-expanded becomes true when nav is open", () => {
    render(<MobileNavToggle links={links} />);
    const button = screen.getByRole("button");
    fireEvent.click(button);
    expect(button).toHaveAttribute("aria-expanded", "true");
    expect(button).toHaveAttribute("aria-label", "Close menu");
  });

  it("nav contains all expected navigation links", () => {
    render(<MobileNavToggle links={links} />);
    fireEvent.click(screen.getByRole("button"));
    expect(screen.getByRole("link", { name: "Gallery" })).toHaveAttribute(
      "href",
      "/gallery",
    );
    expect(screen.getByRole("link", { name: "Artists" })).toHaveAttribute(
      "href",
      "/artists",
    );
    expect(screen.getByRole("link", { name: "Collections" })).toHaveAttribute(
      "href",
      "/collections",
    );
  });

  it("pressing Escape closes the nav", () => {
    render(<MobileNavToggle links={links} />);
    fireEvent.click(screen.getByRole("button"));
    expect(
      screen.getByRole("navigation", { name: "Mobile navigation" }),
    ).toBeInTheDocument();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(
      screen.queryByRole("navigation", { name: "Mobile navigation" }),
    ).not.toBeInTheDocument();
  });

  it("clicking the button again closes the nav", () => {
    render(<MobileNavToggle links={links} />);
    const button = screen.getByRole("button");
    fireEvent.click(button);
    expect(
      screen.getByRole("navigation", { name: "Mobile navigation" }),
    ).toBeInTheDocument();
    fireEvent.click(button);
    expect(
      screen.queryByRole("navigation", { name: "Mobile navigation" }),
    ).not.toBeInTheDocument();
  });

  it("renders no nav links when the menu is closed", () => {
    render(<MobileNavToggle links={links} />);
    expect(screen.queryByRole("link", { name: "Gallery" })).not.toBeInTheDocument();
  });
});
