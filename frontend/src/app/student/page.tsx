"use client";

import { useEffect, useState } from 'react';
import api from '../../services/api';
import QuizRunner from '../../components/student/QuizRunner';

interface Upload {
    id: string;
    file_name: string;
    created_at: string;
}

export default function StudentPage() {
    const [uploads, setUploads] = useState<Upload[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedUploadId, setSelectedUploadId] = useState<string | null>(null);

    useEffect(() => {
        const init = async () => {
            try {
                const res: any = await api.get('/content/uploads');
                setUploads(res.data);
            } catch (err: any) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        }
        init();
    }, []);

    if (selectedUploadId) {
        return (
            <QuizRunner
                uploadId={selectedUploadId}
                onExit={() => setSelectedUploadId(null)}
            />
        );
    }

    return (
        <div>
            <h2 style={{ textAlign: 'center', marginBottom: '2rem' }}>Zona de Estudio</h2>

            {loading ? <p>Cargando actividades...</p> : (
                <div className="grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '1.5rem' }}>
                    {uploads.map(upload => (
                        <div key={upload.id} className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                            <h4 style={{ wordBreak: 'break-all' }}>{upload.file_name}</h4>
                            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                                {new Date(upload.created_at).toLocaleDateString()}
                            </p>
                            <button
                                onClick={() => setSelectedUploadId(upload.id)}
                                className="btn"
                            >
                                Comenzar Actividad
                            </button>
                        </div>
                    ))}
                    {uploads.length === 0 && <p>No hay actividades asignadas.</p>}
                </div>
            )}
        </div>
    );
}
