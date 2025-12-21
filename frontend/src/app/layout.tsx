import './globals.css';
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import Link from 'next/link';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
    title: 'DECIES Platform',
    description: 'AI-Powered Education Platform',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="es">
            <body className={inter.className}>
                <nav style={{ borderBottom: '1px solid var(--border-color)', padding: '1rem' }}>
                    <div className="container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ fontWeight: 'bold', fontSize: '1.25rem' }}>
                            <span style={{ color: 'var(--accent-primary)' }}>DECIES</span> Platform
                        </div>
                        <div style={{ display: 'flex', gap: '1rem' }}>
                            <Link href="/" style={{ color: 'var(--text-secondary)' }}>Home</Link>
                            <Link href="/tutor" style={{ color: 'var(--text-secondary)' }}>Tutor</Link>
                            <Link href="/student" style={{ color: 'var(--text-secondary)' }}>Estudiante</Link>
                            <Link href="/admin" style={{ color: 'var(--text-secondary)' }}>Admin</Link>
                        </div>
                    </div>
                </nav>
                <main className="container" style={{ padding: '2rem 0' }}>
                    {children}
                </main>
            </body>
        </html>
    );
}
