"use client";

import { useCallback, useEffect, useRef, useState } from 'react';
import api from '../../services/api';
import UploadItemsManager from './UploadItemsManager';

interface Upload {
    id: string;
    file_name: string;
    upload_type: string;
    created_at: string;
}

interface UploadListProps {
    refreshSignal?: number;
}

type ProcessingStatus = 'idle' | 'queued' | 'running' | 'succeeded' | 'failed';

interface ProcessingState {
    status: ProcessingStatus;
    job_id?: string | null;
    error?: string | null;
    processed_at?: string | null;
}

export default function UploadList({ refreshSignal }: UploadListProps) {
    const [uploads, setUploads] = useState<Upload[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [itemsUploadId, setItemsUploadId] = useState<string | null>(null);
    const [processingById, setProcessingById] = useState<Record<string, ProcessingState>>({});
    const [actionLoadingById, setActionLoadingById] = useState<Record<string, boolean>>({});
    const [actionErrorById, setActionErrorById] = useState<Record<string, string>>({});

    const fetchProcessing = useCallback(async (uploadIds: string[]) => {
        if (uploadIds.length === 0) return;

        const results = await Promise.allSettled(
            uploadIds.map((id) => api.get(`/content/uploads/${id}/processing`)),
        );

        const next: Record<string, ProcessingState> = {};
        for (let i = 0; i < uploadIds.length; i += 1) {
            const id = uploadIds[i];
            const res = results[i];
            if (res.status === 'fulfilled') {
                next[id] = {
                    status: (res.value.data.status || 'idle') as ProcessingStatus,
                    job_id: res.value.data.job_id ?? null,
                    error: res.value.data.error ?? null,
                    processed_at: res.value.data.processed_at ?? null,
                };
            }
        }
        setProcessingById((prev) => ({ ...prev, ...next }));
    }, []);

    const fetchUploads = useCallback(async () => {
        try {
            setLoading(true);
            const res = await api.get('/content/uploads');
            setUploads(res.data);
            await fetchProcessing(res.data.map((u: Upload) => u.id));
            setError('');
        } catch (err: any) {
            console.error(err);
            const detail = err?.response?.data?.detail;
            if (detail === 'Not enough permissions') {
                setError('Necesitas iniciar sesión como tutor.');
            } else {
                setError(detail || err?.message || 'Error cargando uploads');
            }
        } finally {
            setLoading(false);
        }
    }, [fetchProcessing]);

    const handleProcess = useCallback(
        async (uploadId: string) => {
            setActionLoadingById((prev) => ({ ...prev, [uploadId]: true }));
            setActionErrorById((prev) => ({ ...prev, [uploadId]: '' }));
            try {
                await api.post(`/content/uploads/${uploadId}/process`);
                await fetchProcessing([uploadId]);
            } catch (err: any) {
                console.error(err);
                const detail = err?.response?.data?.detail;
                const message =
                    detail === 'Not enough permissions'
                        ? 'Necesitas iniciar sesión como tutor.'
                        : detail || err?.message || 'Error';
                setActionErrorById((prev) => ({ ...prev, [uploadId]: message }));
            } finally {
                setActionLoadingById((prev) => ({ ...prev, [uploadId]: false }));
            }
        },
        [fetchProcessing],
    );

    useEffect(() => {
        fetchUploads();
    }, [fetchUploads, refreshSignal]);

    const wasProcessingRef = useRef(false);

    useEffect(() => {
        const uploadsIds = uploads.map((u) => u.id);
        if (uploadsIds.length === 0) {
            wasProcessingRef.current = false;
            return undefined;
        }

        const isActive = uploads.some((upload) => {
            const state = processingById[upload.id];
            return state?.status === 'queued' || state?.status === 'running';
        });

        if (!isActive && wasProcessingRef.current) {
            void fetchProcessing(uploadsIds);
        }

        wasProcessingRef.current = isActive;

        if (!isActive) {
            return undefined;
        }

        const handle = window.setInterval(() => {
            fetchProcessing(uploadsIds);
        }, 5000);
        return () => window.clearInterval(handle);
    }, [fetchProcessing, uploads, processingById]);

    if (loading) return <p>Cargando uploads...</p>;
    if (error) return <p style={{ color: 'var(--error)' }}>{error}</p>;
    if (uploads.length === 0) return <p>No hay uploads.</p>;

    const renderStatus = (uploadId: string) => {
        const state = processingById[uploadId];
        const status: ProcessingStatus = state?.status || 'idle';
        const labelByStatus: Record<ProcessingStatus, string> = {
            idle: 'Sin procesar',
            queued: 'En cola',
            running: 'Procesando',
            succeeded: 'Procesado',
            failed: 'Error',
        };
        const colorByStatus: Record<ProcessingStatus, string> = {
            idle: 'var(--text-secondary)',
            queued: 'var(--primary)',
            running: 'var(--primary)',
            succeeded: 'var(--success)',
            failed: 'var(--error)',
        };

        return (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                <span style={{ color: colorByStatus[status], fontWeight: 600 }}>
                    {labelByStatus[status]}
                </span>
                {status === 'succeeded' && state?.processed_at && (
                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                        {new Date(state.processed_at).toLocaleString()}
                    </span>
                )}
                {status === 'failed' && state?.error && (
                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                        {state.error}
                    </span>
                )}
            </div>
        );
    };

    return (
        <div className="card" style={{ marginTop: '2rem' }}>
            <h3>Mis Archivos</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '1rem' }}>
                <thead>
                    <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>
                        <th style={{ padding: '0.5rem' }}>Archivo</th>
                        <th style={{ padding: '0.5rem' }}>Tipo</th>
                        <th style={{ padding: '0.5rem' }}>Fecha</th>
                        <th style={{ padding: '0.5rem' }}>Estado</th>
                        <th style={{ padding: '0.5rem' }}>Acción</th>
                    </tr>
                </thead>
                <tbody>
                    {uploads.map((upload) => {
                        const state = processingById[upload.id];
                        const status: ProcessingStatus = state?.status || 'idle';
                        const actionLoading = !!actionLoadingById[upload.id];
                        const disableProcessing =
                            actionLoading || status === 'queued' || status === 'running';
                        const label =
                            status === 'succeeded' || status === 'failed' ? 'Reprocesar' : 'Procesar';

                        return (
                            <tr
                                key={upload.id}
                                style={{ borderBottom: '1px solid var(--border-color)' }}
                            >
                                <td style={{ padding: '0.5rem' }}>{upload.file_name}</td>
                                <td style={{ padding: '0.5rem' }}>{upload.upload_type}</td>
                                <td style={{ padding: '0.5rem' }}>
                                    {new Date(upload.created_at).toLocaleDateString()}
                                </td>
                                <td style={{ padding: '0.5rem' }}>{renderStatus(upload.id)}</td>
                                <td style={{ padding: '0.5rem' }}>
                                    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                        <button
                                            onClick={() => handleProcess(upload.id)}
                                            disabled={disableProcessing}
                                            className="btn"
                                            style={{ fontSize: '0.875rem', padding: '0.25rem 0.75rem' }}
                                            title={
                                                status === 'queued' || status === 'running'
                                                    ? 'Procesamiento en curso'
                                                    : undefined
                                            }
                                        >
                                            {actionLoading ? 'Iniciando...' : label}
                                        </button>
                                        <button
                                            className="btn btn-secondary"
                                            onClick={() => setItemsUploadId(upload.id)}
                                        >
                                            Ítems
                                        </button>
                                        {actionErrorById[upload.id] && (
                                            <span style={{ color: 'var(--error)' }}>
                                                {actionErrorById[upload.id]}
                                            </span>
                                        )}
                                    </div>
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
            <button
                onClick={fetchUploads}
                style={{
                    marginTop: '1rem',
                    background: 'none',
                    border: 'none',
                    color: 'var(--text-secondary)',
                    cursor: 'pointer',
                }}
            >
                Refrescar lista
            </button>

            {itemsUploadId && (
                <UploadItemsManager uploadId={itemsUploadId} onClose={() => setItemsUploadId(null)} />
            )}
        </div>
    );
}
