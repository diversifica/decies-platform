"use client";

import { useEffect, useState } from 'react';
import AuthPanel from '../../components/auth/AuthPanel';
import api from '../../services/api';
import QuizRunner from '../../components/student/QuizRunner';
import MatchRunner from '../../components/student/MatchRunner';
import ClozeRunner from '../../components/student/ClozeRunner';
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
    const [activeActivity, setActiveActivity] = useState<{
        mode: 'QUIZ' | 'EXAM_STYLE' | 'MATCH' | 'CLOZE' | 'REVIEW';
        upload?: Upload | null;
        subjectId: string;
        termId: string;
    } | null>(null);
    const [me, setMe] = useState<AuthMe | null>(null);
    const [actionError, setActionError] = useState<string>('');
    const [actionLoading, setActionLoading] = useState(false);

    const studentId = me?.student_id || '';

    useEffect(() => {
        const loadUploads = async () => {
            if (!studentId) {
                setUploads([]);
                setLoading(false);
                return;
            }

            setLoading(true);
            try {
                const res: any = await api.get('/content/uploads');
                setUploads(res.data);
                setActionError('');
            } catch (err: any) {
                console.error(err);
                setUploads([]);
            } finally {
                setLoading(false);
            }
        };

        loadUploads();
    }, [studentId]);

    const openActivity = async (upload: Upload, mode: 'QUIZ' | 'EXAM_STYLE' | 'MATCH' | 'CLOZE') => {
        if (!studentId) return;
        setActionError('');
        setActionLoading(true);
        try {
            const res = await api.get(`/content/uploads/${upload.id}/items`);
            const items: any[] = Array.isArray(res.data) ? res.data : [];
            const hasMatch = items.some((i) => i?.type === 'match');
            const hasQuiz = items.some((i) => i?.type === 'multiple_choice' || i?.type === 'true_false');
            const hasCloze = items.some((i) => i?.type === 'cloze');

            if (mode === 'MATCH' && !hasMatch) {
                setActionError('Este contenido aún no tiene ítems MATCH. Por ahora usa Quiz.');
                return;
            }
            if ((mode === 'QUIZ' || mode === 'EXAM_STYLE') && !hasQuiz) {
                setActionError('Este contenido aún no tiene preguntas de Quiz. Pide al tutor que lo procese.');
                return;
            }
            if (mode === 'CLOZE' && !hasCloze) {
                setActionError('Este contenido aún no tiene ítems CLOZE. Por ahora usa Quiz.');
                return;
            }

            setActiveActivity({ mode, upload, subjectId: upload.subject_id, termId: upload.term_id });
        } catch (err: any) {
            console.error(err);
            setActionError(err?.response?.data?.detail || err?.message || 'No se pudo abrir la actividad.');
        } finally {
            setActionLoading(false);
        }
    };

    const openReview = () => {
        if (!studentId) return;
        setActionError('');
        const scope = uploads[0];
        if (!scope) {
            setActionError('Aún no hay contenido disponible para revisar.');
            return;
        }
        setActiveActivity({ mode: 'REVIEW', upload: null, subjectId: scope.subject_id, termId: scope.term_id });
    };

    if (activeActivity) {
        if (!studentId) {
            return <p>No hay estudiante asociado a esta sesión. Inicia sesión como estudiante.</p>;
        }

        if (activeActivity.mode !== 'REVIEW' && !activeActivity.upload?.id) {
            return (
                <div className="card" style={{ maxWidth: '600px', margin: '0 auto' }}>
                    <h3>Error</h3>
                    <p>No se encontró el contenido seleccionado. Vuelve a intentarlo.</p>
                    <button className="btn btn-secondary" onClick={() => setActiveActivity(null)}>
                        Volver
                    </button>
                </div>
            );
        }

        const uploadId = activeActivity.upload?.id;

        return activeActivity.mode === 'MATCH' ? (
            <MatchRunner
                uploadId={uploadId!}
                studentId={studentId}
                subjectId={activeActivity.subjectId}
                termId={activeActivity.termId}
                onExit={() => setActiveActivity(null)}
            />
        ) : activeActivity.mode === 'CLOZE' ? (
            <ClozeRunner
                uploadId={uploadId!}
                studentId={studentId}
                subjectId={activeActivity.subjectId}
                termId={activeActivity.termId}
                onExit={() => setActiveActivity(null)}
            />
        ) : activeActivity.mode === 'EXAM_STYLE' ? (
            <QuizRunner
                uploadId={uploadId}
                studentId={studentId}
                subjectId={activeActivity.subjectId}
                termId={activeActivity.termId}
                onExit={() => setActiveActivity(null)}
                activityCode="EXAM_STYLE"
                examMode
                timeLimitSeconds={10 * 60}
            />
        ) : (
            <QuizRunner
                uploadId={activeActivity.mode === 'REVIEW' ? undefined : uploadId}
                studentId={studentId}
                subjectId={activeActivity.subjectId}
                termId={activeActivity.termId}
                onExit={() => setActiveActivity(null)}
                activityCode={activeActivity.mode === 'REVIEW' ? 'REVIEW' : 'QUIZ'}
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

            {actionError && <p style={{ color: 'var(--error)', marginTop: '1rem' }}>{actionError}</p>}

            <div className="card" style={{ marginTop: '1.25rem', padding: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem' }}>
                    <div>
                        <h4 style={{ margin: 0 }}>Revisión</h4>
                        <p style={{ margin: '0.25rem 0 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                            Repasa priorizando microconceptos vencidos.
                        </p>
                    </div>
                    <button
                        disabled={!studentId || actionLoading || uploads.length === 0}
                        onClick={openReview}
                        className="btn btn-secondary"
                        title={uploads.length === 0 ? 'Sube y procesa contenido para habilitar revisión.' : 'Iniciar sesión de revisión'}
                    >
                        Iniciar revisión
                    </button>
                </div>
                {studentId && uploads.length === 0 && (
                    <p style={{ margin: '0.75rem 0 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                        Aún no hay contenido disponible; pide al tutor que suba y procese material.
                    </p>
                )}
            </div>

            {loading ? <p>Cargando actividades...</p> : (
                <div className="grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '1.5rem' }}>
                    {uploads.map(upload => (
                        <div key={upload.id} className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                            <h4 style={{ wordBreak: 'break-all' }}>{upload.file_name}</h4>
                            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                                {new Date(upload.created_at).toLocaleDateString()}
                            </p>
                            <div style={{ display: 'flex', gap: '0.75rem' }}>
                                <button
                                    disabled={!studentId || actionLoading}
                                    onClick={() => openActivity(upload, 'QUIZ')}
                                    className="btn"
                                >
                                    {actionLoading ? 'Cargando...' : 'Quiz'}
                                </button>
                                <button
                                    disabled={!studentId || actionLoading}
                                    onClick={() => openActivity(upload, 'EXAM_STYLE')}
                                    className="btn btn-secondary"
                                >
                                    {actionLoading ? 'Cargando...' : 'Examen'}
                                </button>
                                <button
                                    disabled={!studentId || actionLoading}
                                    onClick={() => openActivity(upload, 'MATCH')}
                                    className="btn btn-secondary"
                                >
                                    {actionLoading ? 'Cargando...' : 'Match'}
                                </button>
                                <button
                                    disabled={!studentId || actionLoading}
                                    onClick={() => openActivity(upload, 'CLOZE')}
                                    className="btn btn-secondary"
                                >
                                    {actionLoading ? 'Cargando...' : 'Cloze'}
                                </button>
                            </div>
                        </div>
                    ))}
                    {uploads.length === 0 && <p>No hay actividades asignadas.</p>}
                </div>
            )}
        </div>
    );
}
