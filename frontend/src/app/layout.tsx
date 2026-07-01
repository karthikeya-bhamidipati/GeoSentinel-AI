import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GeoSentinel AI — Urban & Vegetation Change Detection",
  description:
    "Cloud-native geospatial analytics platform for urban expansion and vegetation dynamics monitoring in the Hyderabad Metropolitan Region using Sentinel-2 imagery.",
  keywords: [
    "GeoSentinel",
    "Hyderabad",
    "remote sensing",
    "urban change detection",
    "Sentinel-2",
    "land cover",
  ],
  authors: [{ name: "Karthikeya Bhamidipati" }],
  viewport: "width=device-width, initial-scale=1",
  robots: "index, follow",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
