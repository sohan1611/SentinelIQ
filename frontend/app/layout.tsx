import type { Metadata } from "next";
import { Inter, Playfair_Display, IBM_Plex_Mono } from "next/font/google";
import { AuthProvider } from "@/contexts/AuthContext";
import "./globals.css";

const inter = Inter({ 
  subsets: ["latin"], 
  weight: ["400", "500", "600"],
  variable: "--font-sans", 
  display: 'swap' 
});

const playfair = Playfair_Display({ 
  subsets: ["latin"], 
  weight: ["400"],
  variable: "--font-serif", 
  display: 'swap' 
});

const ibmPlexMono = IBM_Plex_Mono({ 
  subsets: ["latin"], 
  weight: ["400", "500", "700"], 
  variable: "--font-mono", 
  display: 'swap' 
});

export const metadata: Metadata = {
  title: "SentinelIQ | Corporate Fraud Early Warning",
  description: "Detect early warning signs of corporate fraud.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${playfair.variable} ${ibmPlexMono.variable}`}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
