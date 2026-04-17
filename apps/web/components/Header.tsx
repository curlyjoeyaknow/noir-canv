import Link from "next/link";

import { MobileNavToggle } from "@/components/MobileNavToggle";

const navLinks = [
  { href: "/", label: "Home" },
  { href: "/pieces", label: "Works" },
  { href: "/artists", label: "Artists" },
  { href: "/collections", label: "Collections" },
];

export function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-border/80 bg-background/95 backdrop-blur-md supports-[backdrop-filter]:bg-background/80">
      <nav className="relative mx-auto flex max-w-7xl items-center justify-between px-6 py-4 md:px-8">
        <Link
          href="/"
          className="font-serif text-xl font-semibold tracking-wide text-foreground transition-colors duration-200 hover:text-accent"
        >
          Noir Canvas
        </Link>

        <ul className="hidden items-center gap-8 md:flex">
          {navLinks.map(({ href, label }) => (
            <li key={href}>
              <Link
                href={href}
                className="relative text-sm font-medium text-muted transition-colors duration-200 hover:text-foreground after:absolute after:-bottom-1 after:left-0 after:h-px after:w-0 after:bg-accent after:transition-all after:duration-300 hover:after:w-full"
              >
                {label}
              </Link>
            </li>
          ))}
        </ul>

        <MobileNavToggle links={navLinks} />
      </nav>
    </header>
  );
}
