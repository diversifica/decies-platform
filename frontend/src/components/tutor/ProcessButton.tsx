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

    const handleProcess = async () => {
        setLoading(true);
        setStatus('processing');
        try {
            await api.post(`/content/uploads/${uploadId}/process`);
            setStatus('success');
            if (onProcessStarted) onProcessStarted();
        } catch (error) {
            console.error(error);
            setStatus('error');
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
            {status === 'error' && <span style={{ color: 'var(--error)', marginLeft: '0.5rem' }}>Error</span>}
        </div>
    );
}
