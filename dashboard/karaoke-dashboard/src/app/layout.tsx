import "@/styles/globals.css";

export const metadata = {
  title: "Karaoke Pipeline Dashboard",
  description: "Pipeline status and management",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        {children}
      </body>
    </html>
  );
}
