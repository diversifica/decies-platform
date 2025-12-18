"use client";

import { useState } from 'react';
import api from '../../services/api';

interface ProcessButtonProps {
    uploadId: string;
    onProcessStarted?: () => void;
}

export default function ProcessButton({ uploadId, onProcessStarted }: ProcessButtonProps) {
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState<'idle' | 'processing' | 'success' | 'error'>('idle');
    const [errorMessage, setErrorMessage] = useState<string>('');

    const handleProcess = async () => {
        setLoading(true);
        setStatus('processing');
        setErrorMessage('');
        try {
            await api.post(`/content/uploads/${uploadId}/process`);
            setStatus('success');
            if (onProcessStarted) onProcessStarted();
        } catch (error: any) {
            console.error(error);
            setStatus('error');
            const detail = error?.response?.data?.detail;
            if (detail === 'Not enough permissions') {
                setErrorMessage('Necesitas iniciar sesión como tutor.');
            } else {
                setErrorMessage(detail || error?.message || 'Error');
            }
        } finally {
            setLoading(false);
        }
    };

    if (status === 'success') {
        return <span style={{ color: 'var(--success)' }}>Procesando...</span>;
    }

    return (
        <div>
            <button
                onClick={handleProcess}
                disabled={loading}
                className="btn"
                style={{ fontSize: '0.875rem', padding: '0.25rem 0.75rem' }}
            >
                {loading ? 'Iniciando...' : 'Procesar'}
            </button>
            {status === 'error' && (
                <span style={{ color: 'var(--error)', marginLeft: '0.5rem' }}>
                    {errorMessage || 'Error'}
                </span>
            )}
        </div>
    );
}
