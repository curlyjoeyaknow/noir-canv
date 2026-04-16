"use client";

import Image from "next/image";
import { useCallback, useEffect, useRef, useState } from "react";

interface LightboxImage {
  src: string;
  alt: string;
}

interface ImageLightboxProps {
  images: LightboxImage[];
  initialIndex?: number;
  onClose: () => void;
}

export function ImageLightbox({
  images,
  initialIndex = 0,
  onClose,
}: ImageLightboxProps) {
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [isZoomed, setIsZoomed] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const previousFocus = useRef<HTMLElement | null>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  const total = images.length;
  const current = images[currentIndex];

  const handlePrev = useCallback(
    () => setCurrentIndex((i) => (i - 1 + total) % total),
    [total],
  );
  const handleNext = useCallback(
    () => setCurrentIndex((i) => (i + 1) % total),
    [total],
  );

  useEffect(() => {
    previousFocus.current = document.activeElement as HTMLElement | null;
    closeButtonRef.current?.focus();
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = "";
      previousFocus.current?.focus();
    };
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      e.preventDefault();
      onClose();
    } else if (e.key === "ArrowLeft" && total > 1) {
      e.preventDefault();
      handlePrev();
    } else if (e.key === "ArrowRight" && total > 1) {
      e.preventDefault();
      handleNext();
    } else if (e.key === "Tab") {
      const focusable = containerRef.current?.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
      );
      if (!focusable || focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    }
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === containerRef.current) onClose();
  };

  return (
    <div
      ref={containerRef}
      role="dialog"
      aria-modal="true"
      aria-label="Image lightbox"
      onKeyDown={handleKeyDown}
      onClick={handleBackdropClick}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm"
    >
      <button
        ref={closeButtonRef}
        type="button"
        onClick={onClose}
        aria-label="Close lightbox"
        className="absolute right-4 top-4 z-10 rounded-full bg-overlay p-2.5 text-foreground transition-all duration-200 hover:bg-surface-hover hover:scale-110"
      >
        <CloseIcon />
      </button>

      {total > 1 && (
        <>
          <button
            type="button"
            onClick={handlePrev}
            aria-label="Previous image"
            className="absolute left-4 top-1/2 z-10 -translate-y-1/2 rounded-full bg-overlay p-2.5 text-foreground transition-all duration-200 hover:bg-surface-hover hover:scale-110"
          >
            <ChevronLeft />
          </button>
          <button
            type="button"
            onClick={handleNext}
            aria-label="Next image"
            className="absolute right-4 top-1/2 z-10 -translate-y-1/2 rounded-full bg-overlay p-2.5 text-foreground transition-all duration-200 hover:bg-surface-hover hover:scale-110"
          >
            <ChevronRight />
          </button>
        </>
      )}

      <div
        className={`relative transition-transform duration-300 ${
          isZoomed
            ? "h-full w-full cursor-zoom-out"
            : "max-h-[90vh] max-w-[90vw] cursor-zoom-in"
        }`}
        onClick={() => setIsZoomed((z) => !z)}
      >
        <Image
          src={current.src}
          alt={current.alt}
          fill
          sizes="100vw"
          className={`object-contain transition-transform duration-300 ${
            isZoomed ? "scale-150" : "scale-100"
          }`}
          priority
        />
      </div>

      {total > 1 && (
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 rounded-full border border-border/40 bg-overlay px-4 py-1.5 text-sm tabular-nums text-foreground">
          {currentIndex + 1} / {total}
        </div>
      )}
    </div>
  );
}

function CloseIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden>
      <path d="M5 5L15 15M15 5L5 15" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
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
