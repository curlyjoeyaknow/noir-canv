import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { MockupViewer } from "./MockupViewer";

vi.mock("./FrameSelector", () => ({
  FrameSelector: ({
    frames,
    onImageClick,
  }: {
    frames: { style: string; imageUrl: string }[];
    onImageClick?: (index: number) => void;
  }) => (
    <div data-testid="frame-selector">
      {frames.map((f) => (
        <button key={f.style} onClick={() => onImageClick?.(0)}>
          {f.style}
        </button>
      ))}
    </div>
  ),
}));

vi.mock("./ImageCarousel", () => ({
  ImageCarousel: ({
    images,
    onImageClick,
  }: {
    images: { src: string; alt: string }[];
    onImageClick?: (index: number) => void;
  }) => (
    <div data-testid="image-carousel">
      {images.map((img, i) => (
        // eslint-disable-next-line @next/next/no-img-element
        <img key={i} src={img.src} alt={img.alt} onClick={() => onImageClick?.(i)} />
      ))}
    </div>
  ),
}));

vi.mock("./ImageLightbox", () => ({
  ImageLightbox: ({ onClose }: { onClose: () => void }) => (
    <div data-testid="image-lightbox">
      <button onClick={onClose} aria-label="Close lightbox">
        Close
      </button>
    </div>
  ),
}));

const framedMockups = [
  { type: "framed", variant: "black", imageUrl: "/images/mockups/framed-black.png" },
  { type: "framed", variant: "white", imageUrl: "/images/mockups/framed-white.png" },
];

const roomMockups = [
  { type: "room", variant: "apartment", imageUrl: "/images/mockups/room-apt.png" },
  { type: "room", variant: "office", imageUrl: "/images/mockups/room-office.png" },
];

const artistHoldingMockups = [
  { type: "artist-holding", variant: "portrait", imageUrl: "/images/mockups/artist.png" },
];

describe("MockupViewer", () => {
  it("renders null when mockups array is empty", () => {
    const { container } = render(
      <MockupViewer pieceTitle="Test Piece" mockups={[]} />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("renders a section with an accessible label", () => {
    render(<MockupViewer pieceTitle="Dusk Amber" mockups={framedMockups} />);
    expect(
      screen.getByRole("region", { name: "Mockup views for Dusk Amber" }),
    ).toBeInTheDocument();
  });

  it("does not render tab bar when only one mockup type is present", () => {
    render(<MockupViewer pieceTitle="Test Piece" mockups={framedMockups} />);
    expect(screen.queryByRole("tablist")).not.toBeInTheDocument();
  });

  it("renders FrameSelector for framed mockups when it is the only type", () => {
    render(<MockupViewer pieceTitle="Test Piece" mockups={framedMockups} />);
    expect(screen.getByTestId("frame-selector")).toBeInTheDocument();
  });

  it("renders tab buttons when mockups of multiple types are present", () => {
    render(
      <MockupViewer
        pieceTitle="Test Piece"
        mockups={[...framedMockups, ...roomMockups]}
      />,
    );
    expect(screen.getByRole("tablist", { name: "Mockup categories" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Framed" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Room Settings" })).toBeInTheDocument();
  });

  it("first available tab is active by default", () => {
    render(
      <MockupViewer
        pieceTitle="Test Piece"
        mockups={[...framedMockups, ...roomMockups]}
      />,
    );
    expect(screen.getByRole("tab", { name: "Framed" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByRole("tab", { name: "Room Settings" })).toHaveAttribute(
      "aria-selected",
      "false",
    );
  });

  it("clicking a tab changes the active panel", () => {
    render(
      <MockupViewer
        pieceTitle="Test Piece"
        mockups={[...framedMockups, ...roomMockups]}
      />,
    );
    fireEvent.click(screen.getByRole("tab", { name: "Room Settings" }));
    expect(screen.getByRole("tab", { name: "Room Settings" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByRole("tab", { name: "Framed" })).toHaveAttribute(
      "aria-selected",
      "false",
    );
    expect(screen.getByTestId("image-carousel")).toBeInTheDocument();
  });

  it("renders Artist tab when artist-holding mockups are present", () => {
    render(
      <MockupViewer
        pieceTitle="Test Piece"
        mockups={[...framedMockups, ...artistHoldingMockups]}
      />,
    );
    expect(screen.getByRole("tab", { name: "Artist" })).toBeInTheDocument();
  });

  it("shows ImageCarousel for room mockups after switching to room tab", () => {
    render(
      <MockupViewer
        pieceTitle="Test Piece"
        mockups={[...framedMockups, ...roomMockups]}
      />,
    );
    fireEvent.click(screen.getByRole("tab", { name: "Room Settings" }));
    expect(screen.getByTestId("image-carousel")).toBeInTheDocument();
    expect(screen.queryByTestId("frame-selector")).not.toBeInTheDocument();
  });

  it("renders tabpanel with correct id for active tab", () => {
    render(
      <MockupViewer
        pieceTitle="Test Piece"
        mockups={[...framedMockups, ...roomMockups]}
      />,
    );
    expect(screen.getByRole("tabpanel")).toHaveAttribute("id", "mockup-panel-framed");
  });

  it("opening lightbox via FrameSelector click shows ImageLightbox", () => {
    render(
      <MockupViewer
        pieceTitle="Test Piece"
        mockups={framedMockups}
      />,
    );
    fireEvent.click(screen.getByText("black"));
    expect(screen.getByTestId("image-lightbox")).toBeInTheDocument();
  });

  it("closing lightbox removes ImageLightbox from DOM", () => {
    render(
      <MockupViewer
        pieceTitle="Test Piece"
        mockups={framedMockups}
      />,
    );
    fireEvent.click(screen.getByText("black"));
    expect(screen.getByTestId("image-lightbox")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Close lightbox" }));
    expect(screen.queryByTestId("image-lightbox")).not.toBeInTheDocument();
  });
});
