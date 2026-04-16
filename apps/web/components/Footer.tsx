import Link from "next/link";

const footerLinks = [
  { href: "/artists", label: "Artists" },
  { href: "/collections", label: "Collections" },
];

const socialLinks = [
  { href: "https://instagram.com/noircanvas", label: "Instagram" },
  { href: "https://x.com/noircanvas", label: "X / Twitter" },
];

export function Footer() {
  return (
    <footer className="border-t border-border/80 bg-surface">
      <div className="mx-auto max-w-7xl px-6 py-16 md:px-8 md:py-20">
        <div className="grid gap-12 sm:grid-cols-2 lg:grid-cols-3 sm:gap-10">
          <div className="sm:col-span-2 lg:col-span-1">
            <p className="font-serif text-lg font-semibold text-foreground">
              Noir Canvas
            </p>
            <p className="mt-3 text-sm leading-relaxed text-muted">
              Curated limited-edition canvas art from independent artists. Each
              piece is numbered, authenticated, and crafted for modern spaces.
            </p>
          </div>

          <nav aria-label="Footer navigation">
            <p className="text-xs font-semibold uppercase tracking-widest text-dim">
              Gallery
            </p>
            <ul className="mt-4 flex flex-col gap-3">
              {footerLinks.map(({ href, label }) => (
                <li key={href}>
                  <Link
                    href={href}
                    className="block py-2 text-sm text-muted transition-colors duration-200 hover:text-accent"
                  >
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>

          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-dim">
              Follow
            </p>
            <ul className="mt-4 flex flex-col gap-3">
              {socialLinks.map(({ href, label }) => (
                <li key={href}>
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block py-2 text-sm text-muted transition-colors duration-200 hover:text-accent"
                  >
                    {label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-14 border-t border-border/60 pt-8 text-center">
          <p className="text-xs text-dim">
            &copy; {new Date().getFullYear()} Noir Canvas. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
