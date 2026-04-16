import type { Metadata } from "next";
import { Inter, Playfair_Display } from "next/font/google";

import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";

import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const playfair = Playfair_Display({
  variable: "--font-playfair",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Noir Canvas — Limited Edition Art",
    template: "%s | Noir Canvas",
  },
  description:
    "Curated limited edition canvas art from independent artists. Each piece is numbered, authenticated, and crafted for modern spaces.",
  openGraph: {
    type: "website",
    siteName: "Noir Canvas",
    title: "Noir Canvas — Limited Edition Art",
    description:
      "Curated limited edition canvas art from independent artists.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${inter.variable} ${playfair.variable} font-sans antialiased bg-background text-foreground`}
      >
        <Header />
        <main className="min-h-screen">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
