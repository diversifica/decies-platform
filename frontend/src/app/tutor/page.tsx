"use client";

import { FormEvent, useCallback, useEffect, useState } from 'react';
import AuthPanel from '../../components/auth/AuthPanel';
import UploadForm from '../../components/tutor/UploadForm';
import UploadList from '../../components/tutor/UploadList';
import MetricsDashboard from '../../components/tutor/MetricsDashboard';
import RecommendationList from '../../components/tutor/RecommendationList';
import TutorReportPanel from '../../components/tutor/TutorReportPanel';
import MicroconceptManager from '../../components/tutor/MicroconceptManager';
import RealGradesPanel from '../../components/tutor/RealGradesPanel';
import { AuthMe } from '../../services/auth';
import {
    assignStudentSubject,
    createSubject,
    deleteSubject,
    fetchStudents,
    fetchSubjects,
    fetchTerms,
    StudentSummary,
    SubjectSummary,
    TermSummary,
    updateSubject,
} from '../../services/catalog';

export default function TutorPage() {
    const [activeTab, setActiveTab] = useState<'content' | 'metrics' | 'recommendations' | 'reports' | 'microconcepts' | 'grades'>('content');

    const [me, setMe] = useState<AuthMe | null>(null);
    const [subjects, setSubjects] = useState<SubjectSummary[]>([]);
    const [terms, setTerms] = useState<TermSummary[]>([]);
    const [subjectStudents, setSubjectStudents] = useState<StudentSummary[]>([]);
    const [allStudents, setAllStudents] = useState<StudentSummary[]>([]);

    const [selectedSubjectId, setSelectedSubjectId] = useState<string>('');
    const [selectedTermId, setSelectedTermId] = useState<string>('');
    const [selectedStudentId, setSelectedStudentId] = useState<string>('');
    const [uploadsRefreshSignal, setUploadsRefreshSignal] = useState<number>(0);
    const [newSubjectName, setNewSubjectName] = useState('');
    const [newSubjectDescription, setNewSubjectDescription] = useState('');
    const [creatingSubject, setCreatingSubject] = useState(false);
    const [subjectFeedback, setSubjectFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
    const [assignFeedback, setAssignFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
    const [assigningSubject, setAssigningSubject] = useState(false);
    const [editingSubjectId, setEditingSubjectId] = useState<string | null>(null);
    const [editingSubjectName, setEditingSubjectName] = useState('');
    const [editingSubjectDescription, setEditingSubjectDescription] = useState('');
    const [subjectEditFeedback, setSubjectEditFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
    const [deletingSubjectId, setDeletingSubjectId] = useState<string | null>(null);

    const getTabStyle = (tabName: string) => ({
        padding: '0.75rem 1.5rem',
        background: 'none',
        border: 'none',
        borderBottom: activeTab === tabName ? '2px solid var(--primary)' : '2px solid transparent',
        color: activeTab === tabName ? 'var(--primary)' : 'var(--text-secondary)',
        fontWeight: activeTab === tabName ? 'bold' as const : 'normal' as const,
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        marginBottom: '-2px'
    });

    const isTutor = (me?.role || '').toLowerCase() === 'tutor';
    const tutorId = me?.tutor_id || '';

    const loadCatalog = useCallback(async () => {
        if (!isTutor) return;

        const [subjectsData, termsData] = await Promise.all([
            fetchSubjects(true),
            fetchTerms(true),
        ]);
        setSubjects(subjectsData);
        setTerms(termsData);

        setSelectedSubjectId((prev) => prev || subjectsData[0]?.id || '');
        setSelectedTermId((prev) => prev || termsData[0]?.id || '');
    }, [isTutor]);

    useEffect(() => {
        loadCatalog();
    }, [loadCatalog]);

    const loadAssignableStudents = useCallback(async () => {
        if (!isTutor) {
            setAllStudents([]);
            return [];
        }
        const studentsData = await fetchStudents(true);
        setAllStudents(studentsData);
        return studentsData;
    }, [isTutor]);

    const loadSubjectStudents = useCallback(async () => {
        if (!isTutor || !selectedSubjectId) {
            setSubjectStudents([]);
            return [];
        }
        const studentsData = await fetchStudents(true, selectedSubjectId);
        setSubjectStudents(studentsData);
        return studentsData;
    }, [isTutor, selectedSubjectId]);

    useEffect(() => {
        loadAssignableStudents();
    }, [loadAssignableStudents]);

    useEffect(() => {
        loadSubjectStudents();
    }, [loadSubjectStudents]);

    const studentOptions = subjectStudents.length ? subjectStudents : allStudents;

    useEffect(() => {
        if (studentOptions.length === 0) {
            setSelectedStudentId('');
            return;
        }
        setSelectedStudentId((prev) => {
            if (prev && studentOptions.some((option) => option.id === prev)) {
                return prev;
            }
            return studentOptions[0].id;
        });
    }, [studentOptions]);

    const assignedStudent = subjectStudents.find((student) => student.id === selectedStudentId);
    const hasAssignedStudent = Boolean(assignedStudent);

    const handleCreateSubject = useCallback(
        async (event: FormEvent<HTMLFormElement>) => {
            event.preventDefault();
            const name = newSubjectName.trim();
            if (!name) {
                setSubjectFeedback({ type: 'error', message: 'El nombre es obligatorio' });
                return;
            }
            setCreatingSubject(true);
            setSubjectFeedback(null);
            try {
                const created = await createSubject({
                    name,
                    description: newSubjectDescription.trim() || undefined,
                });
                await loadCatalog();
                setSelectedSubjectId(created.id);
                setNewSubjectName('');
                setNewSubjectDescription('');
                setSubjectFeedback({
                    type: 'success',
                    message: `Asignatura "${created.name}" creada`,
                });
            } catch (err: any) {
                const detail = err?.response?.data?.detail;
                setSubjectFeedback({
                    type: 'error',
                    message: detail || err?.message || 'No se pudo crear la asignatura',
                });
            } finally {
                setCreatingSubject(false);
            }
        },
        [newSubjectDescription, newSubjectName, loadCatalog],
    );

    const handleAssignSubject = useCallback(async () => {
        if (!selectedStudentId || !selectedSubjectId) {
            setAssignFeedback({ type: 'error', message: 'Selecciona alumno y asignatura' });
            return;
        }
        setAssigningSubject(true);
        setAssignFeedback(null);
        try {
            await assignStudentSubject(selectedStudentId, selectedSubjectId);
            setAssignFeedback({
                type: 'success',
                message: 'Asignatura asignada al alumno seleccionado.',
            });
            await Promise.all([loadSubjectStudents(), loadAssignableStudents()]);
        } catch (err: any) {
            const detail = err?.response?.data?.detail;
            setAssignFeedback({
                type: 'error',
                message: detail || err?.message || 'No se pudo asignar la asignatura',
            });
        } finally {
            setAssigningSubject(false);
        }
    }, [selectedStudentId, selectedSubjectId, loadAssignableStudents, loadSubjectStudents]);

    const startEditingSubject = useCallback((subject: SubjectSummary) => {
        setEditingSubjectId(subject.id);
        setEditingSubjectName(subject.name);
        setEditingSubjectDescription(subject.description ?? '');
        setSubjectEditFeedback(null);
    }, []);

    const handleUpdateSubject = useCallback(
        async (event: FormEvent<HTMLFormElement>) => {
            event.preventDefault();
            if (!editingSubjectId) return;
            const trimmedName = editingSubjectName.trim();
            if (!trimmedName) {
                setSubjectEditFeedback({ type: 'error', message: 'El nombre es obligatorio' });
                return;
            }

            const subjectId = editingSubjectId;
            setSubjectEditFeedback(null);
            try {
                await updateSubject(subjectId, {
                    name: trimmedName,
                    description: editingSubjectDescription.trim() || undefined,
                });
                setSelectedSubjectId(subjectId);
                await loadCatalog();
                setEditingSubjectId(null);
                setEditingSubjectName('');
                setEditingSubjectDescription('');
                setSubjectEditFeedback({
                    type: 'success',
                    message: 'Asignatura actualizada',
                });
            } catch (err: any) {
                const detail = err?.response?.data?.detail;
                setSubjectEditFeedback({
                    type: 'error',
                    message: detail || err?.message || 'No se pudo actualizar la asignatura',
                });
            }
        },
        [editingSubjectDescription, editingSubjectId, editingSubjectName, loadCatalog],
    );

    const handleCancelEdit = useCallback(() => {
        setEditingSubjectId(null);
        setEditingSubjectName('');
        setEditingSubjectDescription('');
        setSubjectEditFeedback(null);
    }, []);

    const handleDeleteSubject = useCallback(
        async (subjectId: string) => {
            if (!window.confirm('¿Seguro que quieres eliminar esta asignatura?')) {
                return;
            }
            setDeletingSubjectId(subjectId);
            setSubjectEditFeedback(null);
            setSubjectFeedback(null);
            setAssignFeedback(null);
            setEditingSubjectId(null);
            setSelectedSubjectId('');
            setSelectedStudentId('');
            try {
                await deleteSubject(subjectId);
                await loadCatalog();
                setSubjectEditFeedback({
                    type: 'success',
                    message: 'Asignatura eliminada',
                });
            } catch (err: any) {
                const detail = err?.response?.data?.detail;
                setSubjectEditFeedback({
                    type: 'error',
                    message: detail || err?.message || 'No se pudo eliminar la asignatura',
                });
            } finally {
                setDeletingSubjectId(null);
            }
        },
        [loadCatalog],
    );

    return (
        <div>
            <h2 style={{ marginBottom: '2rem', textAlign: 'center' }}>Panel del Tutor</h2>

            <AuthPanel
                title="Acceso Tutor"
                defaultEmail="tutor@decies.com"
                defaultPassword="decies"
                onAuth={(loadedMe) => {
                    setMe(loadedMe);
                    setSelectedStudentId('');
                    setUploadsRefreshSignal((v) => v + 1);
                }}
                    onLogout={() => {
                        setMe(null);
                        setSubjects([]);
                        setTerms([]);
                        setSubjectStudents([]);
                        setAllStudents([]);
                        setSelectedSubjectId('');
                        setSelectedTermId('');
                        setSelectedStudentId('');
                        setUploadsRefreshSignal((v) => v + 1);
                    }}
            />

            {me && !isTutor && (
                <div className="card" style={{ marginBottom: '1.5rem', borderLeft: '4px solid var(--error)' }}>
                    <h3 style={{ marginBottom: '0.5rem' }}>Acceso restringido</h3>
                    <p style={{ margin: 0 }}>
                        Has iniciado sesión como <strong>{(me.role || 'N/A').toUpperCase()}</strong>. Para subir y procesar contenido, inicia sesión con un usuario tutor.
                    </p>
                </div>
            )}

            {isTutor && (
                <div className="card" style={{ marginBottom: '1.5rem' }}>
                    <h3 style={{ marginBottom: '1rem' }}>Contexto</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
                        <label>
                            Asignatura
                            <select className="input" value={selectedSubjectId} onChange={(e) => setSelectedSubjectId(e.target.value)}>
                                {subjects.map((s) => (
                                    <option key={s.id} value={s.id}>{s.name}</option>
                                ))}
                            </select>
                        </label>
                        <label>
                            Trimestre
                            <select className="input" value={selectedTermId} onChange={(e) => setSelectedTermId(e.target.value)}>
                                {terms.map((t) => {
                                    const yearLabel = t.academic_year_name ? ` (${t.academic_year_name})` : '';
                                    return (
                                        <option key={t.id} value={t.id}>
                                            {`${t.code} - ${t.name}${yearLabel}`}
                                        </option>
                                    );
                                })}
                            </select>
                        </label>
                        <label>
                            Alumno
                            <select className="input" value={selectedStudentId} onChange={(e) => setSelectedStudentId(e.target.value)}>
                                {studentOptions.length === 0 ? (
                                    <option value="">No hay alumnos disponibles</option>
                                ) : (
                                    studentOptions.map((s) => (
                                        <option key={s.id} value={s.id}>
                                            {s.full_name || s.email || s.id}
                                        </option>
                                    ))
                                )}
                            </select>
                        </label>
                    </div>
                    <form
                        onSubmit={handleCreateSubject}
                        style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}
                    >
                        <h4 style={{ margin: 0 }}>Crear nueva asignatura</h4>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '0.5rem' }}>
                            <label style={{ display: 'flex', flexDirection: 'column' }}>
                                Nombre
                                <input
                                    className="input"
                                    placeholder="Ej. Física I"
                                    value={newSubjectName}
                                    onChange={(e) => setNewSubjectName(e.target.value)}
                                />
                            </label>
                            <label style={{ display: 'flex', flexDirection: 'column' }}>
                                Descripción (opcional)
                                <textarea
                                    className="input"
                                    rows={2}
                                    placeholder="Breve descripción de la asignatura"
                                    value={newSubjectDescription}
                                    onChange={(e) => setNewSubjectDescription(e.target.value)}
                                />
                            </label>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                            <button
                                type="submit"
                                className="btn"
                                disabled={creatingSubject || !newSubjectName.trim()}
                                style={{ fontSize: '0.875rem', padding: '0.25rem 0.75rem' }}
                            >
                                {creatingSubject ? 'Creando...' : 'Crear asignatura'}
                            </button>
                            {subjectFeedback && (
                                <span
                                    style={{
                                        color: subjectFeedback.type === 'success' ? 'var(--success)' : 'var(--error)',
                                    }}
                                >
                                    {subjectFeedback.message}
                                </span>
                            )}
                        </div>
                    </form>
                    <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                            <button
                                type="button"
                                className="btn"
                                disabled={!selectedStudentId || !selectedSubjectId || assigningSubject}
                                onClick={handleAssignSubject}
                                style={{ fontSize: '0.875rem', padding: '0.25rem 0.75rem' }}
                            >
                                {assigningSubject ? 'Asignando...' : 'Asignar asignatura al alumno seleccionado'}
                            </button>
                            {assignFeedback && (
                                <span
                                    style={{
                                        color: assignFeedback.type === 'success' ? 'var(--success)' : 'var(--error)',
                                    }}
                                >
                                    {assignFeedback.message}
                                </span>
                            )}
                        </div>
                        <div>
                            <h4 style={{ margin: '0 0 0.5rem 0' }}>Mis asignaturas</h4>
                            {subjects.length === 0 ? (
                                <p style={{ color: 'var(--text-secondary)', margin: 0 }}>
                                    Aún no has creado ninguna asignatura.
                                </p>
                            ) : (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                    {subjects.map((subject) => (
                                        <div
                                            key={subject.id}
                                            style={{
                                                padding: '0.75rem 1rem',
                                                borderRadius: 'var(--radius-sm)',
                                                border:
                                                    editingSubjectId === subject.id
                                                        ? '2px solid var(--primary)'
                                                        : '1px solid var(--border-color)',
                                                backgroundColor: 'var(--bg-primary)',
                                                display: 'flex',
                                                justifyContent: 'space-between',
                                                alignItems: 'center',
                                                gap: '1rem',
                                            }}
                                        >
                                            <div>
                                                <strong>{subject.name}</strong>
                                                {subject.description && (
                                                    <p
                                                        style={{
                                                            margin: '0.25rem 0 0',
                                                            color: 'var(--text-secondary)',
                                                            fontSize: '0.9rem',
                                                        }}
                                                    >
                                                        {subject.description}
                                                    </p>
                                                )}
                                            </div>
                                            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                                <button
                                                    type="button"
                                                    className="btn btn-secondary"
                                                    onClick={() => startEditingSubject(subject)}
                                                >
                                                    Editar
                                                </button>
                                                <button
                                                    type="button"
                                                    className="btn btn-secondary"
                                                    onClick={() => handleDeleteSubject(subject.id)}
                                                    disabled={deletingSubjectId === subject.id}
                                                >
                                                    {deletingSubjectId === subject.id ? 'Eliminando...' : 'Eliminar'}
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                            {editingSubjectId && (
                                <form
                                    onSubmit={handleUpdateSubject}
                                    style={{
                                        marginTop: '1rem',
                                        display: 'grid',
                                        gridTemplateColumns: '1fr',
                                        gap: '0.5rem',
                                    }}
                                >
                                    <label style={{ display: 'flex', flexDirection: 'column' }}>
                                        Nombre
                                        <input
                                            className="input"
                                            value={editingSubjectName}
                                            onChange={(e) => setEditingSubjectName(e.target.value)}
                                        />
                                    </label>
                                    <label style={{ display: 'flex', flexDirection: 'column' }}>
                                        Descripción (opcional)
                                        <textarea
                                            className="input"
                                            rows={2}
                                            value={editingSubjectDescription}
                                            onChange={(e) => setEditingSubjectDescription(e.target.value)}
                                        />
                                    </label>
                                    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                        <button
                                            type="submit"
                                            className="btn"
                                            style={{ fontSize: '0.875rem', padding: '0.25rem 0.75rem' }}
                                        >
                                            Guardar cambios
                                        </button>
                                        <button
                                            type="button"
                                            className="btn btn-secondary"
                                            onClick={handleCancelEdit}
                                            style={{ fontSize: '0.875rem', padding: '0.25rem 0.75rem' }}
                                        >
                                            Cancelar
                                        </button>
                                    </div>
                                    {subjectEditFeedback && (
                                        <span
                                            style={{
                                                color:
                                                    subjectEditFeedback.type === 'success'
                                                        ? 'var(--success)'
                                                        : 'var(--error)',
                                            }}
                                        >
                                            {subjectEditFeedback.message}
                                        </span>
                                    )}
                                </form>
                            )}
                        </div>
                    </div>
                    {(!selectedStudentId || !selectedSubjectId || !selectedTermId) && (
                        <p style={{ marginTop: '0.75rem', color: 'var(--text-secondary)' }}>
                            Selecciona asignatura, trimestre y alumno para ver métricas, recomendaciones e informes.
                        </p>
                    )}
                </div>
            )}

            {isTutor && (
                <>
                    {/* Tabs */}
                    <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem', borderBottom: '2px solid var(--border-color)' }}>
                        <button
                            onClick={() => setActiveTab('content')}
                            style={getTabStyle('content')}
                        >
                            Contenido
                        </button>
                        <button
                            onClick={() => setActiveTab('metrics')}
                            style={getTabStyle('metrics')}
                        >
                            Métricas y Dominio
                        </button>
                        <button
                            onClick={() => setActiveTab('recommendations')}
                            style={getTabStyle('recommendations')}
                        >
                            Recomendaciones
                        </button>
                        <button
                            onClick={() => setActiveTab('reports')}
                            style={getTabStyle('reports')}
                        >
                            Informe
                        </button>
                        <button
                            onClick={() => setActiveTab('microconcepts')}
                            style={getTabStyle('microconcepts')}
                        >
                            Microconceptos
                        </button>
                        <button
                            onClick={() => setActiveTab('grades')}
                            style={getTabStyle('grades')}
                        >
                            Calificaciones
                        </button>
                    </div>

                    {/* Content */}
                    {activeTab === 'content' && (
                        <div style={{ display: 'grid', gap: '2rem' }}>
                            <section>
                                <UploadForm
                                    subjectId={selectedSubjectId}
                                    termId={selectedTermId}
                                    onUploadSuccess={() => setUploadsRefreshSignal((v) => v + 1)}
                                />
                            </section>
                            <section>
                                <UploadList refreshSignal={uploadsRefreshSignal} />
                            </section>
                        </div>
                    )}

                    {activeTab === 'metrics' && (
                        hasAssignedStudent && selectedSubjectId && selectedTermId ? (
                            <MetricsDashboard
                                studentId={selectedStudentId}
                                subjectId={selectedSubjectId}
                                termId={selectedTermId}
                            />
                        ) : (
                            <p>Asigna al alumno a la asignatura para ver métricas.</p>
                        )
                    )}

                    {activeTab === 'recommendations' && (
                        hasAssignedStudent && selectedSubjectId && selectedTermId && tutorId ? (
                            <RecommendationList
                                studentId={selectedStudentId}
                                subjectId={selectedSubjectId}
                                termId={selectedTermId}
                                tutorId={tutorId}
                            />
                        ) : (
                            <p>Asigna al alumno a la asignatura para ver recomendaciones.</p>
                        )
                    )}

                    {activeTab === 'reports' && (
                        hasAssignedStudent && selectedSubjectId && selectedTermId && tutorId ? (
                            <TutorReportPanel
                                tutorId={tutorId}
                                studentId={selectedStudentId}
                                subjectId={selectedSubjectId}
                                termId={selectedTermId}
                            />
                        ) : (
                            <p>Asigna al alumno a la asignatura para ver informes.</p>
                        )
                    )}

                    {activeTab === 'microconcepts' && (
                        selectedSubjectId && selectedTermId ? (
                            <MicroconceptManager
                                subjectId={selectedSubjectId}
                                termId={selectedTermId}
                            />
                        ) : (
                            <p>Selecciona asignatura y trimestre para gestionar microconceptos.</p>
                        )
                    )}

                    {activeTab === 'grades' && (
                        hasAssignedStudent && selectedSubjectId && selectedTermId ? (
                            <RealGradesPanel
                                studentId={selectedStudentId}
                                subjectId={selectedSubjectId}
                                termId={selectedTermId}
                            />
                        ) : (
                            <p>Asigna al alumno a la asignatura para ver calificaciones.</p>
                        )
                    )}
                </>
            )}
        </div>
    );
}
