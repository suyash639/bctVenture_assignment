import type { Metadata } from "next";
import type { ReactNode } from "react";
import { DataProvider } from "@/components/DataProvider";
import { Shell } from "@/components/Shell";
import "./globals.css";

export const metadata: Metadata = {
  title: "Meta Ads Creative Intelligence",
  description: "Verified Meta Ad Library creatives for five Indian D2C brands: visual features, clusters and traceable observations.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <DataProvider>
          <Shell>{children}</Shell>
        </DataProvider>
      </body>
    </html>
  );
}
