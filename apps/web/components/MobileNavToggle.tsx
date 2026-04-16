"use client";

import { useState, useCallback, useEffect } from "react";
import Link from "next/link";

interface NavLink {
  href: string;
  label: string;
}

interface MobileNavToggleProps {
  links: NavLink[];
}

export function MobileNavToggle({ links }: MobileNavToggleProps) {
  const [open, setOpen] = useState(false);

  const close = useCallback(() => setOpen(false), []);

  useEffect(() => {
    if (!open) return;
    document.body.style.overflow = "hidden";
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open, close]);

  return (
    <div className="md:hidden">
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        aria-expanded={open}
        aria-label={open ? "Close menu" : "Open menu"}
        className="relative flex h-11 w-11 items-center justify-center text-muted transition-colors hover:text-foreground"
      >
        <span
          className={`absolute h-0.5 w-5 rounded-full bg-current transition-all duration-300 ${
            open ? "translate-y-0 rotate-45" : "-translate-y-1.5"
          }`}
        />
        <span
          className={`absolute h-0.5 w-5 rounded-full bg-current transition-opacity duration-200 ${
            open ? "opacity-0" : "opacity-100"
          }`}
        />
        <span
          className={`absolute h-0.5 w-5 rounded-full bg-current transition-all duration-300 ${
            open ? "translate-y-0 -rotate-45" : "translate-y-1.5"
          }`}
        />
      </button>

      {open && (
        <>
          <div
            className="fixed inset-0 top-[57px] z-40 bg-black/40"
            onClick={close}
            aria-hidden="true"
          />
          <nav
            className="absolute left-0 right-0 top-full z-50 animate-fade-in border-b border-border/80 bg-background/98 backdrop-blur-md"
            aria-label="Mobile navigation"
          >
            <ul className="flex flex-col px-6 py-4">
              {links.map(({ href, label }) => (
                <li key={href} className="border-b border-border/40 last:border-b-0">
                  <Link
                    href={href}
                    onClick={close}
                    className="block py-3.5 text-base font-medium text-muted transition-colors duration-200 hover:text-foreground"
                  >
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </>
      )}
    </div>
  );
}
