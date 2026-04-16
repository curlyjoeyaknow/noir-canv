import Link from "next/link";

export default function NotFound() {
  return (
    <section className="mx-auto flex max-w-7xl flex-col items-center justify-center px-6 py-32 text-center md:px-8">
      <p className="text-sm font-semibold uppercase tracking-widest text-accent">
        404
      </p>
      <h1 className="mt-4 font-serif text-4xl font-bold tracking-tight text-foreground md:text-5xl">
        Page not found
      </h1>
      <p className="mt-4 max-w-md text-muted">
        The page you&apos;re looking for doesn&apos;t exist or has been moved.
      </p>
      <div className="mt-10 flex items-center gap-4">
        <Link
          href="/"
          className="rounded-sm bg-accent px-6 py-3 text-sm font-semibold text-background transition-colors hover:bg-accent-muted"
        >
          Go Home
        </Link>
        <Link
          href="/artists"
          className="rounded-sm border border-border px-6 py-3 text-sm font-semibold text-foreground transition-colors hover:border-accent hover:text-accent"
        >
          Browse Artists
        </Link>
      </div>
    </section>
  );
}
