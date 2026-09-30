import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BAA Pipeline Dashboard",
  description: "Canada B2B Business Data Pipeline",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background font-sans antialiased">
        <nav className="border-b bg-white px-6 py-3 flex items-center gap-6">
          <span className="font-semibold text-primary text-lg">BAA Pipeline</span>
          <a href="/" className="text-sm text-muted-foreground hover:text-foreground">Dashboard</a>
          <a href="/businesses" className="text-sm text-muted-foreground hover:text-foreground">Businesses</a>
          <a href="/sources" className="text-sm text-muted-foreground hover:text-foreground">Sources</a>
        </nav>
        <main className="mx-auto max-w-7xl px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
