/**
 * Root Layout
 *
 * Main application layout with navigation
 */

import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import Link from 'next/link';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'PublicWorks AI - Public Contract Analysis',
  description: 'AI-powered platform for analyzing public contracts and detecting risks',
};

function Navigation() {
  const links = [
    { href: '/', label: 'Dashboard' },
    { href: '/analytics', label: 'Analytics' },
    { href: '/contracts', label: 'Contracts' },
    { href: '/providers', label: 'Providers' },
  ];

  return (
    <nav className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <Link href="/" className="text-xl font-bold text-primary-600">
                PublicWorks AI
              </Link>
            </div>
            <div className="hidden sm:ml-8 sm:flex sm:space-x-8">
              {links.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-700 hover:text-gray-900 hover:border-b-2 hover:border-primary-500 transition-colors"
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </div>
          <div className="flex items-center">
            <span className="text-sm text-gray-500">v1.0</span>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen flex flex-col">
          <Navigation />
          <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>
          <footer className="bg-white border-t border-gray-200 py-4">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm text-gray-500">
              © 2024 PublicWorks AI. Built for transparency in public procurement.
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
