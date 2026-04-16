import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { ImageCarousel } from "./ImageCarousel";

vi.mock("next/image", () => ({
  default: ({
    src,
    alt,
    onClick,
  }: {
    src: string;
    alt: string;
    onClick?: React.MouseEventHandler<HTMLImageElement>;
  }) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src} alt={alt} onClick={onClick} />
  ),
}));

const images = [
  { src: "/images/pieces/one.png", alt: "Image one" },
  { src: "/images/pieces/two.png", alt: "Image two" },
  { src: "/images/pieces/three.png", alt: "Image three" },
];

describe("ImageCarousel", () => {
  it("renders null when images array is empty", () => {
    const { container } = render(<ImageCarousel images={[]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders the first image on mount", () => {
    render(<ImageCarousel images={images} />);
    expect(screen.getByAltText("Image one")).toBeInTheDocument();
  });

  it("has an accessible region label", () => {
    render(<ImageCarousel images={images} />);
    expect(
      screen.getByRole("region", { name: "Image carousel" }),
    ).toBeInTheDocument();
  });

  it("clicking Next image button advances to the next image", () => {
    render(<ImageCarousel images={images} />);
    fireEvent.click(screen.getByRole("button", { name: "Next image" }));
    expect(screen.getByAltText("Image two")).toBeInTheDocument();
  });

  it("clicking Previous image button goes to the previous image", () => {
    render(<ImageCarousel images={images} />);
    fireEvent.click(screen.getByRole("button", { name: "Next image" }));
    fireEvent.click(screen.getByRole("button", { name: "Previous image" }));
    expect(screen.getByAltText("Image one")).toBeInTheDocument();
  });

  it("wraps around from last to first on Next", () => {
    render(<ImageCarousel images={images} />);
    fireEvent.click(screen.getByRole("button", { name: "Next image" }));
    fireEvent.click(screen.getByRole("button", { name: "Next image" }));
    fireEvent.click(screen.getByRole("button", { name: "Next image" }));
    expect(screen.getByAltText("Image one")).toBeInTheDocument();
  });

  it("wraps around from first to last on Previous", () => {
    render(<ImageCarousel images={images} />);
    fireEvent.click(screen.getByRole("button", { name: "Previous image" }));
    expect(screen.getByAltText("Image three")).toBeInTheDocument();
  });

  it("renders dot indicators for each image", () => {
    render(<ImageCarousel images={images} />);
    const dots = screen.getAllByRole("tab");
    expect(dots).toHaveLength(3);
  });

  it("first dot is selected by default", () => {
    render(<ImageCarousel images={images} />);
    const dots = screen.getAllByRole("tab");
    expect(dots[0]).toHaveAttribute("aria-selected", "true");
    expect(dots[1]).toHaveAttribute("aria-selected", "false");
    expect(dots[2]).toHaveAttribute("aria-selected", "false");
  });

  it("dot indicator updates when navigating to a different image", () => {
    render(<ImageCarousel images={images} />);
    fireEvent.click(screen.getByRole("button", { name: "Next image" }));
    const dots = screen.getAllByRole("tab");
    expect(dots[0]).toHaveAttribute("aria-selected", "false");
    expect(dots[1]).toHaveAttribute("aria-selected", "true");
  });

  it("clicking a dot indicator navigates to that image", () => {
    render(<ImageCarousel images={images} />);
    const dots = screen.getAllByRole("tab");
    fireEvent.click(dots[2]);
    expect(screen.getByAltText("Image three")).toBeInTheDocument();
    expect(dots[2]).toHaveAttribute("aria-selected", "true");
  });

  it("calls onImageClick with current index when image is clicked", () => {
    const onImageClick = vi.fn();
    render(<ImageCarousel images={images} onImageClick={onImageClick} />);
    fireEvent.click(screen.getByAltText("Image one"));
    expect(onImageClick).toHaveBeenCalledWith(0);
  });

  it("calls onImageClick with updated index after navigating", () => {
    const onImageClick = vi.fn();
    render(<ImageCarousel images={images} onImageClick={onImageClick} />);
    fireEvent.click(screen.getByRole("button", { name: "Next image" }));
    fireEvent.click(screen.getByAltText("Image two"));
    expect(onImageClick).toHaveBeenCalledWith(1);
  });

  it("container has tabIndex 0 making it keyboard focusable", () => {
    render(<ImageCarousel images={images} />);
    const container = screen.getByRole("region", { name: "Image carousel" });
    expect(container).toHaveAttribute("tabindex", "0");
  });

  it("container has aria-roledescription of carousel", () => {
    render(<ImageCarousel images={images} />);
    const container = screen.getByRole("region", { name: "Image carousel" });
    expect(container).toHaveAttribute("aria-roledescription", "carousel");
  });

  it("does not render nav buttons or dots for a single image", () => {
    render(<ImageCarousel images={[images[0]]} />);
    expect(
      screen.queryByRole("button", { name: "Next image" }),
    ).not.toBeInTheDocument();
    expect(screen.queryAllByRole("tab")).toHaveLength(0);
  });
});
