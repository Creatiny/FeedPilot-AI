import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "FeedPilot AI - Formula Calculator for Feed Manufacturers",
  description: "Calculate animal feed formulas in 10 seconds instead of 1 hour. NRC standards, USDA prices. Start your free trial today.",
  keywords: "feed formula, animal nutrition, feed calculator, NRC standards, USDA prices, livestock feed, poultry feed, swine feed",
  authors: [{ name: "FeedPilot AI" }],
  openGraph: {
    title: "FeedPilot AI - 360x Faster Feed Formula Calculation",
    description: "Professional feed formula calculator for SME manufacturers. NRC standards, real-time USDA prices.",
    type: "website",
    locale: "en_US",
  },
  twitter: {
    card: "summary_large_image",
    title: "FeedPilot AI - Formula Calculator",
    description: "Calculate feed formulas in 10 seconds instead of 1 hour.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
