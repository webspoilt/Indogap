import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Idea Scraper - Find Startup Opportunities in India",
  description: "Discover untapped startup opportunities in India by analyzing global trends and identifying gaps in the Indian market.",
  keywords: ["Idea Scraper", "Startup", "India", "Market Gap", "Opportunity Finder", "IndoGap"],
  authors: [{ name: "IndoGap Team" }],
  icons: {
    icon: "/favicon.ico",
  },
  openGraph: {
    title: "Idea Scraper",
    description: "Find startup opportunities by identifying gaps in the Indian market",
    siteName: "Idea Scraper",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Idea Scraper",
    description: "Find startup opportunities by identifying gaps in the Indian market",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-background text-foreground`}
      >
        {children}
        <Toaster />
      </body>
    </html>
  );
}
