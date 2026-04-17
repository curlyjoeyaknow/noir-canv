"use client";

import { useState } from "react";
import Link from "next/link";

import type { Piece } from "@/lib/schemas";
import { formatPrice } from "@/lib/schemas";

interface CheckoutFormProps {
  piece: Piece;
  artistName: string;
}

type FormState = "idle" | "submitting" | "success";

export function CheckoutForm({ piece, artistName }: CheckoutFormProps) {
  const [state, setState] = useState<FormState>("idle");
  const [orderName, setOrderName] = useState("");
  const [orderEmail, setOrderEmail] = useState("");
  const [orderRef] = useState(
    () => "NC-" + Math.random().toString(36).slice(2, 8).toUpperCase(),
  );

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setState("submitting");
    const data = Object.fromEntries(new FormData(e.currentTarget));
    setOrderName(data.firstName as string);
    setOrderEmail(data.email as string);
    // TODO: swap for Shopify / Stripe API call
    await new Promise((r) => setTimeout(r, 1400));
    setState("success");
  }

  if (state === "success") {
    return (
      <div className="space-y-8">
        {/* Confirmation hero */}
        <div className="rounded-sm border border-accent/30 bg-surface p-8 text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-accent/10 ring-1 ring-accent/30">
            <svg
              className="h-8 w-8 text-accent"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.8}
              aria-hidden="true"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" />
            </svg>
          </div>
          <h2 className="mt-4 font-serif text-2xl font-bold text-foreground">
            Order Complete
          </h2>
          <p className="mt-1 text-sm text-dim">Reference: {orderRef}</p>
        </div>

        {/* Order summary */}
        <div className="rounded-sm border border-border/60 bg-surface/50 divide-y divide-border/40">
          <div className="px-5 py-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-dim">Artwork</p>
            <p className="mt-1 font-serif text-lg text-foreground">{piece.title}</p>
            <p className="text-sm text-muted">by {artistName}</p>
          </div>
          <div className="px-5 py-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-dim">Edition</p>
            <p className="mt-1 text-sm text-foreground">
              #{piece.editionsSold + 1} of {piece.editionSize}
            </p>
          </div>
          <div className="px-5 py-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-dim">Total</p>
            <p className="mt-1 font-semibold text-foreground">
              {formatPrice(piece.priceCents, piece.currency)}
            </p>
          </div>
          <div className="px-5 py-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-dim">Confirmation sent to</p>
            <p className="mt-1 text-sm text-foreground">{orderEmail}</p>
          </div>
        </div>

        {/* Next steps */}
        <div className="rounded-sm border border-border/60 p-5 space-y-2 text-sm text-muted">
          <p className="font-semibold text-foreground">What happens next</p>
          <ol className="space-y-2 list-decimal list-inside">
            <li>Our team will email <span className="text-foreground">{orderEmail}</span> within 24 hours to confirm your order.</li>
            <li>We&apos;ll arrange payment and shipping details with you directly.</li>
            <li>Your edition is reserved for 48 hours from now.</li>
          </ol>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row">
          <Link
            href="/pieces"
            className="flex-1 rounded-sm border border-border bg-surface px-5 py-3 text-center text-sm font-medium text-foreground transition-colors hover:border-border-hover hover:text-accent"
          >
            Continue Browsing
          </Link>
          <Link
            href="/"
            className="flex-1 rounded-sm border border-accent bg-accent px-5 py-3 text-center text-sm font-semibold text-background transition-colors hover:bg-accent-hover"
          >
            Back to Home
          </Link>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Piece summary */}
      <div className="rounded-sm border border-border/60 bg-surface/50 p-4">
        <p className="text-xs font-semibold uppercase tracking-wider text-dim">Your Order</p>
        <p className="mt-1.5 font-serif text-lg text-foreground">{piece.title}</p>
        <p className="text-sm text-muted">by {artistName}</p>
        <div className="mt-2 flex items-baseline justify-between">
          <p className="font-semibold text-foreground">
            {formatPrice(piece.priceCents, piece.currency)}
          </p>
          <p className="text-xs text-dim">
            Ed. {piece.editionsSold + 1} / {piece.editionSize}
          </p>
        </div>
      </div>

      {/* Fields */}
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="firstName" className="block text-xs font-semibold uppercase tracking-wider text-dim">
            First Name <span className="text-accent">*</span>
          </label>
          <input
            id="firstName"
            name="firstName"
            type="text"
            required
            autoComplete="given-name"
            className="mt-1.5 w-full rounded-sm border border-border bg-surface px-3 py-2.5 text-sm text-foreground placeholder-dim transition-colors focus:border-accent focus:outline-none"
            placeholder="Jane"
          />
        </div>
        <div>
          <label htmlFor="lastName" className="block text-xs font-semibold uppercase tracking-wider text-dim">
            Last Name <span className="text-accent">*</span>
          </label>
          <input
            id="lastName"
            name="lastName"
            type="text"
            required
            autoComplete="family-name"
            className="mt-1.5 w-full rounded-sm border border-border bg-surface px-3 py-2.5 text-sm text-foreground placeholder-dim transition-colors focus:border-accent focus:outline-none"
            placeholder="Doe"
          />
        </div>
      </div>

      <div>
        <label htmlFor="email" className="block text-xs font-semibold uppercase tracking-wider text-dim">
          Email <span className="text-accent">*</span>
        </label>
        <input
          id="email"
          name="email"
          type="email"
          required
          autoComplete="email"
          className="mt-1.5 w-full rounded-sm border border-border bg-surface px-3 py-2.5 text-sm text-foreground placeholder-dim transition-colors focus:border-accent focus:outline-none"
          placeholder="jane@example.com"
        />
      </div>

      <div>
        <label htmlFor="country" className="block text-xs font-semibold uppercase tracking-wider text-dim">
          Country <span className="text-accent">*</span>
        </label>
        <select
          id="country"
          name="country"
          required
          className="mt-1.5 w-full rounded-sm border border-border bg-surface px-3 py-2.5 text-sm text-foreground transition-colors focus:border-accent focus:outline-none"
        >
          <option value="">Select country…</option>
          <option>Australia</option>
          <option>Canada</option>
          <option>France</option>
          <option>Germany</option>
          <option>Japan</option>
          <option>New Zealand</option>
          <option>United Kingdom</option>
          <option>United States</option>
          <option>Other</option>
        </select>
      </div>

      <div>
        <label htmlFor="notes" className="block text-xs font-semibold uppercase tracking-wider text-dim">
          Notes <span className="text-dim font-normal normal-case">(optional)</span>
        </label>
        <textarea
          id="notes"
          name="notes"
          rows={2}
          className="mt-1.5 w-full resize-none rounded-sm border border-border bg-surface px-3 py-2.5 text-sm text-foreground placeholder-dim transition-colors focus:border-accent focus:outline-none"
          placeholder="Framing preferences, delivery questions…"
        />
      </div>

      <button
        type="submit"
        disabled={state === "submitting"}
        className="w-full rounded-sm border border-accent bg-accent px-6 py-4 text-sm font-semibold uppercase tracking-widest text-background transition-all duration-200 hover:bg-accent-hover hover:border-accent-hover disabled:cursor-wait disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 focus:ring-offset-background"
      >
        {state === "submitting" ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 100 16v-4l-3 3 3 3v-4a8 8 0 01-8-8z" />
            </svg>
            Processing…
          </span>
        ) : (
          "Complete Purchase"
        )}
      </button>

      <p className="text-center text-xs text-dim">
        No payment is taken now — our team will be in touch to finalise.
      </p>
    </form>
  );
}
