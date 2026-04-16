import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { ImageLightbox } from "./ImageLightbox";

vi.mock("next/image", () => ({
  default: ({ src, alt }: { src: string; alt: string }) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src} alt={alt} />
  ),
}));

const images = [
  { src: "/images/pieces/one.png", alt: "Piece one" },
  { src: "/images/pieces/two.png", alt: "Piece two" },
  { src: "/images/pieces/three.png", alt: "Piece three" },
];

describe("ImageLightbox", () => {
  it("renders a dialog with the initial image", () => {
    const onClose = vi.fn();
    render(<ImageLightbox images={images} onClose={onClose} />);
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByAltText("Piece one")).toBeInTheDocument();
  });

  it("renders with the specified initialIndex", () => {
    const onClose = vi.fn();
    render(<ImageLightbox images={images} initialIndex={1} onClose={onClose} />);
    expect(screen.getByAltText("Piece two")).toBeInTheDocument();
  });

  it("dialog has an accessible aria-label", () => {
    const onClose = vi.fn();
    render(<ImageLightbox images={images} onClose={onClose} />);
    expect(screen.getByRole("dialog")).toHaveAttribute("aria-label", "Image lightbox");
  });

  it("dialog has aria-modal attribute", () => {
    const onClose = vi.fn();
    render(<ImageLightbox images={images} onClose={onClose} />);
    expect(screen.getByRole("dialog")).toHaveAttribute("aria-modal", "true");
  });

  it("close button calls onClose when clicked", () => {
    const onClose = vi.fn();
    render(<ImageLightbox images={images} onClose={onClose} />);
    fireEvent.click(screen.getByRole("button", { name: "Close lightbox" }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("pressing Escape calls onClose", () => {
    const onClose = vi.fn();
    render(<ImageLightbox images={images} onClose={onClose} />);
    fireEvent.keyDown(screen.getByRole("dialog"), { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("clicking Next image button advances to the next image", () => {
    const onClose = vi.fn();
    render(<ImageLightbox images={images} onClose={onClose} />);
    fireEvent.click(screen.getByRole("button", { name: "Next image" }));
    expect(screen.getByAltText("Piece two")).toBeInTheDocument();
  });

  it("clicking Previous image button goes to the previous image", () => {
    const onClose = vi.fn();
    render(<ImageLightbox images={images} initialIndex={1} onClose={onClose} />);
    fireEvent.click(screen.getByRole("button", { name: "Previous image" }));
    expect(screen.getByAltText("Piece one")).toBeInTheDocument();
  });

  it("wraps from last image to first on Next", () => {
    const onClose = vi.fn();
    render(<ImageLightbox images={images} initialIndex={2} onClose={onClose} />);
    fireEvent.click(screen.getByRole("button", { name: "Next image" }));
    expect(screen.getByAltText("Piece one")).toBeInTheDocument();
  });

  it("wraps from first image to last on Previous", () => {
    const onClose = vi.fn();
    render(<ImageLightbox images={images} initialIndex={0} onClose={onClose} />);
    fireEvent.click(screen.getByRole("button", { name: "Previous image" }));
    expect(screen.getByAltText("Piece three")).toBeInTheDocument();
  });

  it("ArrowRight key advances to next image", () => {
    const onClose = vi.fn();
    render(<ImageLightbox images={images} onClose={onClose} />);
    fireEvent.keyDown(screen.getByRole("dialog"), { key: "ArrowRight" });
    expect(screen.getByAltText("Piece two")).toBeInTheDocument();
  });

  it("ArrowLeft key goes to previous image", () => {
    const onClose = vi.fn();
    render(<ImageLightbox images={images} initialIndex={1} onClose={onClose} />);
    fireEvent.keyDown(screen.getByRole("dialog"), { key: "ArrowLeft" });
    expect(screen.getByAltText("Piece one")).toBeInTheDocument();
  });

  it("shows image counter when there are multiple images", () => {
    const onClose = vi.fn();
    render(<ImageLightbox images={images} onClose={onClose} />);
    expect(screen.getByText(/1.*\/.*3/)).toBeInTheDocument();
  });

  it("does not show prev/next buttons for a single image", () => {
    const onClose = vi.fn();
    render(<ImageLightbox images={[images[0]]} onClose={onClose} />);
    expect(
      screen.queryByRole("button", { name: "Next image" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Previous image" }),
    ).not.toBeInTheDocument();
  });

  it("clicking the backdrop calls onClose", () => {
    const onClose = vi.fn();
    render(<ImageLightbox images={images} onClose={onClose} />);
    const backdrop = screen.getByRole("dialog");
    fireEvent.click(backdrop);
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
