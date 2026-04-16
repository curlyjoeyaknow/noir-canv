"use client";

import { useMemo, useState } from "react";

import { FrameSelector } from "./FrameSelector";
import { ImageCarousel } from "./ImageCarousel";
import { ImageLightbox } from "./ImageLightbox";

interface MockupItem {
  type: string;
  variant: string;
  imageUrl: string;
}

interface MockupViewerProps {
  pieceTitle: string;
  mockups: MockupItem[];
}

const TAB_CONFIG = [
  { key: "framed", label: "Framed" },
  { key: "room", label: "Room Settings" },
  { key: "artist-holding", label: "Artist" },
] as const;

type TabKey = (typeof TAB_CONFIG)[number]["key"];

export function MockupViewer({ pieceTitle, mockups }: MockupViewerProps) {
  const grouped = useMemo(() => {
    const map: Record<string, MockupItem[]> = {};
    for (const m of mockups) {
      (map[m.type] ??= []).push(m);
    }
    return map;
  }, [mockups]);

  const availableTabs = TAB_CONFIG.filter((t) => grouped[t.key]?.length);

  const [activeTab, setActiveTab] = useState<TabKey>(
    availableTabs[0]?.key ?? "framed",
  );
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [lightboxIndex, setLightboxIndex] = useState(0);

  const allImages = useMemo(
    () =>
      mockups.map((m) => ({
        src: m.imageUrl,
        alt: `${pieceTitle} — ${m.variant}`,
      })),
    [mockups, pieceTitle],
  );

  if (mockups.length === 0) return null;

  const openLightbox = (imageUrl: string) => {
    const idx = mockups.findIndex((m) => m.imageUrl === imageUrl);
    setLightboxIndex(idx === -1 ? 0 : idx);
    setLightboxOpen(true);
  };

  const activeItems = grouped[activeTab] ?? [];

  const framedAsFrames = (grouped["framed"] ?? []).map((m) => ({
    style: m.variant,
    imageUrl: m.imageUrl,
  }));

  const toCarouselImages = (items: MockupItem[]) =>
    items.map((m) => ({
      src: m.imageUrl,
      alt: `${pieceTitle} — ${m.variant}`,
    }));

  const handleFrameClick = (index: number) => {
    const item = grouped["framed"]?.[index];
    if (item) openLightbox(item.imageUrl);
  };

  const handleCarouselClick = (index: number) => {
    const item = activeItems[index];
    if (item) openLightbox(item.imageUrl);
  };

  return (
    <section aria-label={`Mockup views for ${pieceTitle}`} className="space-y-4">
      {availableTabs.length > 1 && (
        <div
          role="tablist"
          aria-label="Mockup categories"
          className="flex gap-1 rounded-sm border border-border/60 bg-surface p-1"
        >
          {availableTabs.map((tab) => (
            <button
              key={tab.key}
              type="button"
              role="tab"
              aria-selected={activeTab === tab.key}
              aria-controls={`mockup-panel-${tab.key}`}
              onClick={() => setActiveTab(tab.key)}
              className={`rounded-sm px-4 py-2 text-sm font-medium transition-all duration-200 ${
                activeTab === tab.key
                  ? "bg-card text-foreground shadow-sm"
                  : "text-muted hover:text-foreground"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      )}

      <div
        id={`mockup-panel-${activeTab}`}
        role="tabpanel"
        aria-label={`${availableTabs.find((t) => t.key === activeTab)?.label} mockups`}
      >
        {activeTab === "framed" && framedAsFrames.length > 0 ? (
          <FrameSelector
            frames={framedAsFrames}
            onImageClick={handleFrameClick}
          />
        ) : (
          <ImageCarousel
            images={toCarouselImages(activeItems)}
            onImageClick={handleCarouselClick}
          />
        )}
      </div>

      {lightboxOpen && (
        <ImageLightbox
          images={allImages}
          initialIndex={lightboxIndex}
          onClose={() => setLightboxOpen(false)}
        />
      )}
    </section>
  );
}
