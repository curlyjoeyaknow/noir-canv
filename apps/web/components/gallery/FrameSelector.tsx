"use client";

import Image from "next/image";
import { useState } from "react";

interface FrameOption {
  style: string;
  imageUrl: string;
}

interface FrameSelectorProps {
  frames: FrameOption[];
  className?: string;
  onImageClick?: (index: number) => void;
}

export function FrameSelector({
  frames,
  className,
  onImageClick,
}: FrameSelectorProps) {
  const [selectedIndex, setSelectedIndex] = useState(0);

  if (frames.length === 0) return null;

  const active = frames[selectedIndex];

  return (
    <div
      role="group"
      aria-label="Frame options"
      className={className}
    >
      <div
        role="button"
        tabIndex={0}
        aria-label={`View ${active.style} frame full size`}
        className="relative aspect-[3/4] w-full cursor-pointer overflow-hidden rounded-sm bg-card transition-shadow duration-300 hover:shadow-lg hover:shadow-black/20"
        onClick={() => onImageClick?.(selectedIndex)}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            onImageClick?.(selectedIndex);
          }
        }}
      >
        <Image
          src={active.imageUrl}
          alt={`${active.style} frame`}
          fill
          sizes="(max-width: 1024px) 100vw, 576px"
          className="object-cover"
        />
      </div>

      <div
        role="radiogroup"
        aria-label="Frame style"
        className="mt-4 flex gap-3 overflow-x-auto"
      >
        {frames.map((frame, i) => (
          <button
            key={frame.style}
            type="button"
            role="radio"
            aria-checked={i === selectedIndex}
            aria-label={`${frame.style} frame`}
            onClick={() => setSelectedIndex(i)}
            className={`flex flex-col items-center gap-1.5 rounded-sm p-1.5 transition-all duration-200 ${
              i === selectedIndex
                ? "ring-2 ring-accent ring-offset-2 ring-offset-background"
                : "opacity-60 hover:opacity-100"
            }`}
          >
            <div className="relative h-20 w-14 overflow-hidden rounded-sm bg-surface">
              <Image
                src={frame.imageUrl}
                alt={`${frame.style} frame thumbnail`}
                fill
                sizes="56px"
                className="object-cover"
              />
            </div>
            <span className={`text-xs transition-colors duration-200 ${i === selectedIndex ? "text-foreground" : "text-muted"}`}>{frame.style}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
