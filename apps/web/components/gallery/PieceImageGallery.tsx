"use client";

import Image from "next/image";
import { useCallback, useMemo, useRef, useState } from "react";

interface MockupItem {
  type: string;
  variant: string;
  imageUrl: string;
}

interface GalleryItem {
  src: string;
  alt: string;
  label: string;
  isMockup: boolean;
}

interface PieceImageGalleryProps {
  pieceTitle: string;
  printImageUrl: string;
  mockups: MockupItem[];
}

export function PieceImageGallery({
  pieceTitle,
  printImageUrl,
  mockups,
}: PieceImageGalleryProps) {
  const items: GalleryItem[] = useMemo(
    () => [
      { src: printImageUrl, alt: pieceTitle, label: "Print", isMockup: false },
      ...mockups.map((m) => ({
        src: m.imageUrl,
        alt: `${pieceTitle} — ${m.variant}`,
        label: m.variant,
        isMockup: true,
      })),
    ],
    [printImageUrl, mockups, pieceTitle],
  );

  const [activeIndex, setActiveIndex] = useState(0);
  const touchStartX = useRef<number | null>(null);
  const total = items.length;

  const goTo = useCallback(
    (index: number) => setActiveIndex((index + total) % total),
    [total],
  );
  const handlePrev = useCallback(() => goTo(activeIndex - 1), [goTo, activeIndex]);
  const handleNext = useCallback(() => goTo(activeIndex + 1), [goTo, activeIndex]);

  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
  };
  const handleTouchEnd = (e: React.TouchEvent) => {
    if (touchStartX.current === null) return;
    const diff = touchStartX.current - e.changedTouches[0].clientX;
    if (Math.abs(diff) > 50) diff > 0 ? handleNext() : handlePrev();
    touchStartX.current = null;
  };

  const active = items[activeIndex];

  return (
    <div
      className="space-y-4"
      onKeyDown={(e) => {
        if (e.key === "ArrowLeft") { e.preventDefault(); handlePrev(); }
        if (e.key === "ArrowRight") { e.preventDefault(); handleNext(); }
      }}
    >
      {/* Main image */}
      <div
        className="relative"
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
      >
        {active.isMockup ? (
          <div className="relative aspect-[3/4] w-full overflow-hidden rounded-sm bg-surface">
            <Image
              src={active.src}
              alt={active.alt}
              fill
              sizes="(max-width: 1024px) 100vw, 576px"
              className="object-contain transition-opacity duration-200"
              priority
            />
          </div>
        ) : (
          <div className="artwork-frame w-full">
            <div className="artwork-mat">
              <div className="relative aspect-[2/3] overflow-hidden ring-[1.5px] ring-black/60">
                <Image
                  src={active.src}
                  alt={active.alt}
                  fill
                  sizes="(max-width: 1024px) 100vw, 576px"
                  className="object-contain"
                  priority
                />
              </div>
            </div>
          </div>
        )}

        {/* Prev / next arrows — only when multiple images */}
        {total > 1 && (
          <>
            <button
              type="button"
              onClick={handlePrev}
              aria-label="Previous image"
              className="absolute left-3 top-1/2 z-10 -translate-y-1/2 rounded-full bg-black/60 p-2.5 text-white transition-all duration-200 hover:bg-black/80 hover:scale-110"
            >
              <ChevronLeft />
            </button>
            <button
              type="button"
              onClick={handleNext}
              aria-label="Next image"
              className="absolute right-3 top-1/2 z-10 -translate-y-1/2 rounded-full bg-black/60 p-2.5 text-white transition-all duration-200 hover:bg-black/80 hover:scale-110"
            >
              <ChevronRight />
            </button>
          </>
        )}
      </div>

      {/* Thumbnail strip */}
      {total > 1 && (
        <div
          role="radiogroup"
          aria-label="Image gallery"
          className="flex gap-2 overflow-x-auto pb-1"
        >
          {items.map((item, i) => (
            <button
              key={`${item.src}-${i}`}
              type="button"
              role="radio"
              aria-checked={i === activeIndex}
              aria-label={item.label}
              onClick={() => setActiveIndex(i)}
              className={`relative h-[72px] w-[54px] flex-none overflow-hidden transition-all duration-200 ${
                i === activeIndex
                  ? "ring-2 ring-accent ring-offset-1 ring-offset-background opacity-100"
                  : "opacity-40 hover:opacity-70"
              }`}
            >
              {!item.isMockup ? (
                <div className="h-full w-full bg-[#2a1d0e] p-[3px]">
                  <div className="h-full w-full bg-[#f5f1e8] p-[3px]">
                    <div className="relative h-full w-full ring-[1px] ring-black/60">
                      <Image
                        src={item.src}
                        alt={item.alt}
                        fill
                        sizes="54px"
                        className="object-contain"
                      />
                    </div>
                  </div>
                </div>
              ) : (
                <Image
                  src={item.src}
                  alt={item.alt}
                  fill
                  sizes="54px"
                  className="object-cover rounded-sm"
                />
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function ChevronLeft() {
  return (
    <svg width="18" height="18" viewBox="0 0 20 20" fill="none" aria-hidden>
      <path d="M12.5 15L7.5 10L12.5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ChevronRight() {
  return (
    <svg width="18" height="18" viewBox="0 0 20 20" fill="none" aria-hidden>
      <path d="M7.5 5L12.5 10L7.5 15" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
