import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/shared/Sidebar";

export const metadata: Metadata = {
  title: "Vitalytics — Lab Intelligence Engine",
  description: "3-Tier Clinical Decision Support System",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div className="flex h-screen overflow-hidden">
          <Sidebar />
          <main className="flex-1 overflow-y-auto" style={{ padding: "32px 40px" }}>
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
