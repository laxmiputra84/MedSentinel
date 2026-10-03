import type { Metadata } from 'next';
import './globals.css';
import { AuthProvider } from '@/lib/authContext';
import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { AIAssistantModal } from '@/components/ai/AIAssistantModal';

export const metadata: Metadata = {
  title: 'MedSentinel — Affordable Healthcare & Cost Intelligence Platform',
  description: 'Compare hospital treatment costs across 10,000+ verified hospitals, evaluate government scheme eligibility, find top health insurance plans, and book consultations.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Manrope:wght@400;600;700;800&display=swap"
          rel="stylesheet"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-gradient-to-br from-gray-900 via-gray-800 to-black font-['Inter'] text-white min-h-screen flex flex-col justify-between">
        <AuthProvider>
          <Navbar />
          <main className="flex-grow">{children}</main>
          <Footer />
          <AIAssistantModal />
        </AuthProvider>
      </body>
    </html>
  );
}

