import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "VidyaMarksheet | B.Sc. Nursing Marksheet Generation System (INC & SGPGIMS)",
  description:
    "Modern institution-grade marksheet generation and evaluation system compliant with Indian Nursing Council (INC) Gazette and SGPGIMS Lucknow regulations. Developed at VidyaLabs.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 antialiased">
        {children}
      </body>
    </html>
  );
}
