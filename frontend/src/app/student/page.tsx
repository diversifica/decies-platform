"use client";

import { useEffect, useState } from 'react';
import AuthPanel from '../../components/auth/AuthPanel';
import api from '../../services/api';
import QuizRunner from '../../components/student/QuizRunner';
import { AuthMe } from '../../services/auth';

interface Upload {
    id: string;
    file_name: string;
    subject_id: string;
    term_id: string;
    created_at: string;
}

export default function StudentPage() {
    const [uploads, setUploads] = useState<Upload[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedUpload, setSelectedUpload] = useState<Upload | null>(null);
    const [me, setMe] = useState<AuthMe | null>(null);

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

    const studentId = me?.student_id || '';

    if (selectedUpload) {
        if (!studentId) {
            return <p>No hay estudiante asociado a esta sesión. Inicia sesión como estudiante.</p>;
        }
        return (
            <QuizRunner
                uploadId={selectedUpload.id}
                studentId={studentId}
                subjectId={selectedUpload.subject_id}
                termId={selectedUpload.term_id}
                onExit={() => setSelectedUpload(null)}
            />
        );
    }

    return (
        <div>
            <h2 style={{ textAlign: 'center', marginBottom: '2rem' }}>Zona de Estudio</h2>

            <AuthPanel
                title="Acceso Estudiante"
                defaultEmail="student@decies.com"
                defaultPassword="decies"
                onAuth={(loadedMe) => setMe(loadedMe)}
                onLogout={() => setMe(null)}
            />

            {loading ? <p>Cargando actividades...</p> : (
                <div className="grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '1.5rem' }}>
                    {uploads.map(upload => (
                        <div key={upload.id} className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                            <h4 style={{ wordBreak: 'break-all' }}>{upload.file_name}</h4>
                            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                                {new Date(upload.created_at).toLocaleDateString()}
                            </p>
                            <button
                                disabled={!studentId}
                                onClick={() => setSelectedUpload(upload)}
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
