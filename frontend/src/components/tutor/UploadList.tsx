"use client";

import { useEffect, useState } from 'react';
import api from '../../services/api';
import ProcessButton from './ProcessButton';
import UploadItemsManager from './UploadItemsManager';

interface Upload {
    id: string;
    file_name: string;
    upload_type: string;
    created_at: string;
    // Add other fields as needed
}

interface UploadListProps {
    refreshSignal?: number;
}

export default function UploadList({ refreshSignal }: UploadListProps) {
    const [uploads, setUploads] = useState<Upload[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [itemsUploadId, setItemsUploadId] = useState<string | null>(null);

    const fetchUploads = async () => {
        try {
            setLoading(true);
            const res = await api.get('/content/uploads');
            setUploads(res.data);
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
    };

    useEffect(() => {
        fetchUploads();
    }, [refreshSignal]);

    if (loading) return <p>Cargando uploads...</p>;
    if (error) return <p style={{ color: 'var(--error)' }}>{error}</p>;
    if (uploads.length === 0) return <p>No hay uploads.</p>;

    return (
        <div className="card" style={{ marginTop: '2rem' }}>
            <h3>Mis Archivos</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '1rem' }}>
                <thead>
                    <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>
                        <th style={{ padding: '0.5rem' }}>Archivo</th>
                        <th style={{ padding: '0.5rem' }}>Tipo</th>
                        <th style={{ padding: '0.5rem' }}>Fecha</th>
                        <th style={{ padding: '0.5rem' }}>Acción</th>
                    </tr>
                </thead>
                <tbody>
                    {uploads.map(upload => (
                        <tr key={upload.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                            <td style={{ padding: '0.5rem' }}>{upload.file_name}</td>
                            <td style={{ padding: '0.5rem' }}>{upload.upload_type}</td>
                            <td style={{ padding: '0.5rem' }}>{new Date(upload.created_at).toLocaleDateString()}</td>
                            <td style={{ padding: '0.5rem' }}>
                                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                    <ProcessButton uploadId={upload.id} />
                                    <button className="btn btn-secondary" onClick={() => setItemsUploadId(upload.id)}>
                                        Ítems
                                    </button>
                                </div>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
            <button onClick={fetchUploads} style={{ marginTop: '1rem', background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                Refrescar lista
            </button>

            {itemsUploadId && (
                <UploadItemsManager uploadId={itemsUploadId} onClose={() => setItemsUploadId(null)} />
            )}
        </div>
    );
}
