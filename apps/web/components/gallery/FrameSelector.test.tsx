import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { FrameSelector } from "./FrameSelector";

vi.mock("next/image", () => ({
  default: ({ src, alt }: { src: string; alt: string }) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src} alt={alt} />
  ),
}));

const frames = [
  { style: "Unframed", imageUrl: "/images/mockups/unframed.png" },
  { style: "Black", imageUrl: "/images/mockups/black.png" },
  { style: "Natural Wood", imageUrl: "/images/mockups/natural-wood.png" },
];

describe("FrameSelector", () => {
  it("renders null when frames array is empty", () => {
    const { container } = render(<FrameSelector frames={[]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders all frame option buttons", () => {
    render(<FrameSelector frames={frames} />);
    expect(screen.getByRole("radio", { name: "Unframed frame" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Black frame" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Natural Wood frame" })).toBeInTheDocument();
  });

  it("first frame is selected by default with aria-checked true", () => {
    render(<FrameSelector frames={frames} />);
    expect(screen.getByRole("radio", { name: "Unframed frame" })).toHaveAttribute(
      "aria-checked",
      "true",
    );
    expect(screen.getByRole("radio", { name: "Black frame" })).toHaveAttribute(
      "aria-checked",
      "false",
    );
    expect(screen.getByRole("radio", { name: "Natural Wood frame" })).toHaveAttribute(
      "aria-checked",
      "false",
    );
  });

  it("clicking a frame option selects it and deselects the previous", () => {
    render(<FrameSelector frames={frames} />);
    fireEvent.click(screen.getByRole("radio", { name: "Black frame" }));
    expect(screen.getByRole("radio", { name: "Black frame" })).toHaveAttribute(
      "aria-checked",
      "true",
    );
    expect(screen.getByRole("radio", { name: "Unframed frame" })).toHaveAttribute(
      "aria-checked",
      "false",
    );
  });

  it("renders the main image with alt text matching the selected frame", () => {
    render(<FrameSelector frames={frames} />);
    expect(screen.getByAltText("Unframed frame")).toBeInTheDocument();
  });

  it("main image alt updates when a different frame is selected", () => {
    render(<FrameSelector frames={frames} />);
    fireEvent.click(screen.getByRole("radio", { name: "Natural Wood frame" }));
    expect(screen.getByAltText("Natural Wood frame")).toBeInTheDocument();
  });

  it("clicking the main image calls onImageClick with the current selected index", () => {
    const onImageClick = vi.fn();
    render(<FrameSelector frames={frames} onImageClick={onImageClick} />);
    fireEvent.click(screen.getByRole("radio", { name: "Black frame" }));
    fireEvent.click(screen.getByAltText("Black frame"));
    expect(onImageClick).toHaveBeenCalledWith(1);
  });

  it("does not throw when onImageClick is not provided and main image is clicked", () => {
    render(<FrameSelector frames={frames} />);
    expect(() => fireEvent.click(screen.getByAltText("Unframed frame"))).not.toThrow();
  });

  it("renders a radiogroup for frame style selection", () => {
    render(<FrameSelector frames={frames} />);
    expect(screen.getByRole("radiogroup", { name: "Frame style" })).toBeInTheDocument();
  });
});
