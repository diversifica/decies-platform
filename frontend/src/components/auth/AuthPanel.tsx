"use client";

import { useEffect, useState } from 'react';

import { AuthMe, clearAccessToken, fetchMe, getAccessToken, login, setAccessToken } from '../../services/auth';

interface AuthPanelProps {
    title?: string;
    defaultEmail?: string;
    defaultPassword?: string;
    onAuth: (me: AuthMe) => void;
    onLogout?: () => void;
}

export default function AuthPanel({ title = 'Acceso', defaultEmail = '', defaultPassword = '', onAuth, onLogout }: AuthPanelProps) {
    const [email, setEmail] = useState(defaultEmail);
    const [password, setPassword] = useState(defaultPassword);
    const [me, setMe] = useState<AuthMe | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        const init = async () => {
            const token = getAccessToken();
            if (!token) return;
            try {
                const loadedMe = await fetchMe();
                setMe(loadedMe);
                onAuth(loadedMe);
            } catch {
                clearAccessToken();
            }
        };
        init();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            const token = await login(email, password);
            setAccessToken(token);
            const loadedMe = await fetchMe();
            setMe(loadedMe);
            onAuth(loadedMe);
        } catch (err: any) {
            const message = err.response?.data?.detail || err.message || 'Error de autenticación';
            setError(message);
        } finally {
            setLoading(false);
        }
    };

    const handleLogout = () => {
        clearAccessToken();
        setMe(null);
        onLogout?.();
    };

    if (me) {
        return (
            <div className="card" style={{ marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
                    <div>
                        <div style={{ fontWeight: 600 }}>{me.email}</div>
                        <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                            Rol: {me.role || 'N/A'}
                        </div>
                    </div>
                    <button className="btn btn-secondary" onClick={handleLogout}>
                        Cerrar sesión
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ marginBottom: '1rem' }}>{title}</h3>
            <form onSubmit={handleLogin} style={{ display: 'grid', gap: '0.75rem' }}>
                <label>
                    Email
                    <input className="input" value={email} onChange={(e) => setEmail(e.target.value)} />
                </label>
                <label>
                    Password
                    <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
                </label>
                <button className="btn" disabled={loading}>
                    {loading ? 'Entrando...' : 'Entrar'}
                </button>
                {error && <div style={{ color: 'var(--error)' }}>{error}</div>}
            </form>
        </div>
    );
}

