import type { Metadata } from "next";
import "../styles/index.css";
import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "sonner";


export const metadata: Metadata = {
  title: "Viora - Document Intelligence",
  description: "Intelligence for your documents",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider>
          {children}
          <Toaster position="bottom-right" richColors />
        </ThemeProvider>
      </body>
    </html>
  );
}
