"use client";

import { useState } from "react";

import type { Piece } from "@/lib/schemas";
import { formatPrice } from "@/lib/schemas";

interface CheckoutFormProps {
  piece: Piece;
  artistName: string;
}

type FormState = "idle" | "submitting" | "success" | "error";

export function CheckoutForm({ piece, artistName }: CheckoutFormProps) {
  const [state, setState] = useState<FormState>("idle");
  const [email, setEmail] = useState("");

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setState("submitting");

    const form = e.currentTarget;
    const data = Object.fromEntries(new FormData(form));

    // Placeholder — no real payment yet.
    // TODO: Replace with Shopify Storefront API or Stripe checkout session.
    await new Promise((r) => setTimeout(r, 1200));

    setEmail(data.email as string);
    setState("success");
  }

  if (state === "success") {
    return (
      <div className="rounded-sm border border-accent/40 bg-surface p-8 text-center">
        <svg
          className="mx-auto mb-4 h-12 w-12 text-accent"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1.5}
          aria-hidden="true"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" />
        </svg>
        <h2 className="font-serif text-2xl font-semibold text-foreground">
          Edition Reserved
        </h2>
        <p className="mt-3 text-muted">
          Thank you. We&apos;ll contact you at{" "}
          <span className="font-medium text-foreground">{email}</span> within 24
          hours to complete your purchase of{" "}
          <span className="italic">{piece.title}</span>.
        </p>
        <p className="mt-2 text-sm text-dim">
          No payment has been taken. Your edition will be held for 48 hours.
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Piece summary */}
      <div className="rounded-sm border border-border/60 bg-surface/50 p-4">
        <p className="text-xs font-semibold uppercase tracking-wider text-dim">
          Reserving
        </p>
        <p className="mt-1.5 font-serif text-lg text-foreground">{piece.title}</p>
        <p className="text-sm text-muted">by {artistName}</p>
        <p className="mt-2 font-semibold text-foreground">
          {formatPrice(piece.priceCents, piece.currency)}
          <span className="ml-2 text-xs font-normal text-dim">
            Ed. {piece.editionsSold + 1}/{piece.editionSize}
          </span>
        </p>
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
          rows={3}
          className="mt-1.5 w-full rounded-sm border border-border bg-surface px-3 py-2.5 text-sm text-foreground placeholder-dim transition-colors focus:border-accent focus:outline-none resize-none"
          placeholder="Framing preferences, delivery questions…"
        />
      </div>

      <p className="text-xs text-dim">
        No payment is taken now. We&apos;ll contact you to finalise the sale and arrange
        delivery. Your edition will be held for 48 hours after we reach out.
      </p>

      <button
        type="submit"
        disabled={state === "submitting"}
        className="w-full rounded-sm border border-accent bg-accent px-6 py-4 text-sm font-semibold uppercase tracking-widest text-background transition-all duration-200 hover:bg-accent-hover hover:border-accent-hover disabled:cursor-wait disabled:opacity-70 focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 focus:ring-offset-background"
      >
        {state === "submitting" ? "Reserving…" : "Reserve My Edition"}
      </button>
    </form>
  );
}
