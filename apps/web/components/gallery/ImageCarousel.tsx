"use client";

import Image from "next/image";
import { useCallback, useRef, useState } from "react";

interface CarouselImage {
  src: string;
  alt: string;
}

interface ImageCarouselProps {
  images: CarouselImage[];
  className?: string;
  onImageClick?: (index: number) => void;
  priority?: boolean;
}

export function ImageCarousel({
  images,
  className,
  onImageClick,
  priority = false,
}: ImageCarouselProps) {
  const [activeIndex, setActiveIndex] = useState(0);
  const touchStartX = useRef<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const total = images.length;

  const goTo = useCallback(
    (index: number) => setActiveIndex((index + total) % total),
    [total],
  );
  const handlePrev = useCallback(() => goTo(activeIndex - 1), [goTo, activeIndex]);
  const handleNext = useCallback(() => goTo(activeIndex + 1), [goTo, activeIndex]);

  if (total === 0) return null;

  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    if (touchStartX.current === null) return;
    const diff = touchStartX.current - e.changedTouches[0].clientX;
    if (Math.abs(diff) > 50) {
      diff > 0 ? handleNext() : handlePrev();
    }
    touchStartX.current = null;
  };

  return (
    <div
      ref={containerRef}
      role="region"
      aria-label="Image carousel"
      aria-roledescription="carousel"
      className={`relative w-full ${className ?? ""}`}
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "ArrowLeft") {
          e.preventDefault();
          handlePrev();
        } else if (e.key === "ArrowRight") {
          e.preventDefault();
          handleNext();
        }
      }}
    >
      <div aria-live="polite" aria-atomic="true" className="sr-only">
        {`Slide ${activeIndex + 1} of ${total}`}
      </div>

      <div
        className={`relative aspect-[3/4] w-full overflow-hidden rounded-sm bg-card ${onImageClick ? "cursor-pointer" : ""}`}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
      >
        <Image
          src={images[activeIndex].src}
          alt={images[activeIndex].alt}
          fill
          sizes="(max-width: 1024px) 100vw, 576px"
          className="object-cover transition-opacity duration-300"
          priority={priority && activeIndex === 0}
          onClick={() => onImageClick?.(activeIndex)}
        />
      </div>

      {total > 1 && (
        <>
          <button
            type="button"
            onClick={handlePrev}
            aria-label="Previous image"
            className="absolute left-3 top-1/2 hidden -translate-y-1/2 rounded-full bg-overlay p-2.5 text-foreground transition-all duration-200 hover:bg-surface-hover hover:scale-110 md:block"
          >
            <ChevronLeft />
          </button>
          <button
            type="button"
            onClick={handleNext}
            aria-label="Next image"
            className="absolute right-3 top-1/2 hidden -translate-y-1/2 rounded-full bg-overlay p-2.5 text-foreground transition-all duration-200 hover:bg-surface-hover hover:scale-110 md:block"
          >
            <ChevronRight />
          </button>
        </>
      )}

      {total > 1 && (
        <div
          role="tablist"
          aria-label="Slide indicators"
          className="mt-3 flex justify-center gap-2"
        >
          {images.map((_, i) => (
            <button
              key={i}
              type="button"
              role="tab"
              aria-selected={i === activeIndex}
              aria-label={`Go to image ${i + 1}`}
              onClick={() => goTo(i)}
              className="flex min-h-[44px] min-w-[44px] items-center justify-center"
            >
              <span
                className={`h-2 rounded-full transition-all duration-300 ${
                  i === activeIndex
                    ? "w-6 bg-accent"
                    : "w-2 bg-border hover:bg-border-hover"
                }`}
              />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function ChevronLeft() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden>
      <path d="M12.5 15L7.5 10L12.5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ChevronRight() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden>
      <path d="M7.5 5L12.5 10L7.5 15" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
