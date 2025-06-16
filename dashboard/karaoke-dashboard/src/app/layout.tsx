import '../styles/globals.css'
import ThemeToggle from '../components/ThemeToggle'
import '@fontsource/inter/variable.css';

export const metadata = {
  title: 'Karaoke Pipeline Dashboard',
  description: 'Pipeline status and management',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-plex-dark text-white">
        {/* Sidebar */}
        <aside className="hidden md:flex flex-col w-60 h-screen bg-sidebar border-r border-[#23272a] shadow-lg">
          <div className="p-6 flex items-center gap-3 border-b border-[#23272a]">
            <img src="https://rorecclesia.com/demo/wp-content/uploads/2025/06/kp_logo_color.png" alt="Logo" className="h-10" />
            <span className="text-lg font-bold text-brand">Karaoke Pipeline</span>
          </div>
          <nav className="flex-1 flex flex-col gap-1 mt-6">
            <a href="/" className="px-6 py-3 rounded-lg text-base hover:bg-surface transition-all">Dashboard</a>
            <a href="#upload" className="px-6 py-3 rounded-lg text-base hover:bg-surface transition-all">Upload</a>
            <a href="#metrics" className="px-6 py-3 rounded-lg text-base hover:bg-surface transition-all">Metrics</a>
            <a href="#settings" className="px-6 py-3 rounded-lg text-base hover:bg-surface transition-all">Settings</a>
          </nav>
          <div className="p-4">
            <ThemeToggle />
          </div>
        </aside>
        {/* Main */}
        <main className="container mx-auto p-4">{children}</main>
          {/* Header */}
          <header className="w-full flex items-center justify-between px-6 py-4 bg-header shadow-sm border-b border-[#23272a]">
            <div className="md:hidden flex items-center gap-2">
              <img src="https://rorecclesia.com/demo/wp-content/uploads/2025/06/kp_logo_color.png" alt="Logo" className="h-8" />
              <span className="text-lg font-bold text-brand">Karaoke Pipeline</span>
            </div>
            <span className="hidden md:block text-xl font-semibold">Admin Dashboard</span>
            <ThemeToggle />
          </header>
          <section className="flex-1 w-full p-4 max-w-5xl mx-auto">
            {children}
          </section>
        </main>
      </body>
    </html>
  )
}
