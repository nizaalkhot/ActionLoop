import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";
import { CheckSquare, BarChart3, Sparkles } from "lucide-react";

export const metadata: Metadata = {
  title: "ActionLoop | Meeting Notes → Tasks",
  description: "Deterministic LLM pipeline turning messy transcripts into deduplicated project management tasks.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-900 font-sans antialiased min-h-screen flex flex-col">
        <header className="border-b border-slate-200 bg-white sticky top-0 z-30 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <Link href="/" className="flex items-center space-x-3">
              <div className="bg-indigo-600 text-white p-2 rounded-lg shadow-sm">
                <CheckSquare className="w-5 h-5" />
              </div>
              <div>
                <span className="font-bold text-lg tracking-tight text-slate-900">ActionLoop</span>
                <span className="ml-2 text-xs font-medium px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
                  Notes → Tasks
                </span>
              </div>
            </Link>

            <nav className="flex items-center space-x-6 text-sm font-medium">
              <Link href="/" className="text-slate-600 hover:text-indigo-600 transition-colors">
                Dashboard & Pipeline
              </Link>
              <Link href="/#eval-metrics" className="flex items-center space-x-1.5 text-slate-600 hover:text-indigo-600 transition-colors">
                <BarChart3 className="w-4 h-4" />
                <span>Accuracy & Evals</span>
              </Link>
              <div className="flex items-center space-x-2 pl-4 border-l border-slate-200 text-xs text-slate-500">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span>Linear Integration Active</span>
              </div>
            </nav>
          </div>
        </header>

        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>

        <footer className="border-t border-slate-200 bg-white py-6 text-center text-xs text-slate-500">
          ActionLoop Mini-SaaS &copy; 2026. Built with Next.js, FastAPI & Google Gemini.
        </footer>
      </body>
    </html>
  );
}

