import Link from 'next/link';

export default function Home() {
    return (
        <div style={{ textAlign: 'center', marginTop: '4rem' }}>
            <h1 style={{ fontSize: '3rem', marginBottom: '1rem' }}>
                Bienvenido a <span style={{ color: 'var(--accent-primary)' }}>DECIES</span>
            </h1>
            <p style={{ fontSize: '1.25rem', color: 'var(--text-secondary)', marginBottom: '3rem' }}>
                Plataforma de Educación Personalizada con IA
            </p>

            <div style={{ display: 'flex', justifyContent: 'center', gap: '2rem' }}>
                <Link href="/tutor" className="btn" style={{ fontSize: '1.25rem', padding: '1rem 2rem' }}>
                    Soy Tutor
                </Link>
                <Link href="/student" className="btn btn-secondary" style={{ fontSize: '1.25rem', padding: '1rem 2rem' }}>
                    Soy Estudiante
                </Link>
            </div>
        </div>
    );
}
