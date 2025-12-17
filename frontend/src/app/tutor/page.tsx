"use client";

import { useEffect, useState } from 'react';
import AuthPanel from '../../components/auth/AuthPanel';
import UploadForm from '../../components/tutor/UploadForm';
import UploadList from '../../components/tutor/UploadList';
import MetricsDashboard from '../../components/tutor/MetricsDashboard';
import RecommendationList from '../../components/tutor/RecommendationList';
import TutorReportPanel from '../../components/tutor/TutorReportPanel';
import { AuthMe } from '../../services/auth';
import { fetchStudents, fetchSubjects, fetchTerms, StudentSummary, SubjectSummary, TermSummary } from '../../services/catalog';

export default function TutorPage() {
    const [activeTab, setActiveTab] = useState<'content' | 'metrics' | 'recommendations' | 'reports'>('content');

    const [me, setMe] = useState<AuthMe | null>(null);
    const [subjects, setSubjects] = useState<SubjectSummary[]>([]);
    const [terms, setTerms] = useState<TermSummary[]>([]);
    const [students, setStudents] = useState<StudentSummary[]>([]);

    const [selectedSubjectId, setSelectedSubjectId] = useState<string>('');
    const [selectedTermId, setSelectedTermId] = useState<string>('');
    const [selectedStudentId, setSelectedStudentId] = useState<string>('');

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

    useEffect(() => {
        const loadCatalog = async () => {
            if (!isTutor) return;

            const [subjectsData, termsData] = await Promise.all([
                fetchSubjects(true),
                fetchTerms(true),
            ]);
            setSubjects(subjectsData);
            setTerms(termsData);

            setSelectedSubjectId((prev) => prev || subjectsData[0]?.id || '');
            setSelectedTermId((prev) => prev || termsData[0]?.id || '');
        };

        loadCatalog();
    }, [isTutor]);

    useEffect(() => {
        const loadStudents = async () => {
            if (!isTutor) return;
            if (!selectedSubjectId) return;

            const studentsData = await fetchStudents(true, selectedSubjectId);
            setStudents(studentsData);
            setSelectedStudentId((prev) => prev || studentsData[0]?.id || '');
        };

        loadStudents();
    }, [isTutor, selectedSubjectId]);

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
                }}
                onLogout={() => {
                    setMe(null);
                    setSubjects([]);
                    setTerms([]);
                    setStudents([]);
                    setSelectedSubjectId('');
                    setSelectedTermId('');
                    setSelectedStudentId('');
                }}
            />

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
                                {terms.map((t) => (
                                    <option key={t.id} value={t.id}>{t.code} - {t.name}</option>
                                ))}
                            </select>
                        </label>
                        <label>
                            Alumno
                            <select className="input" value={selectedStudentId} onChange={(e) => setSelectedStudentId(e.target.value)}>
                                {students.map((s) => (
                                    <option key={s.id} value={s.id}>{s.full_name || s.email || s.id}</option>
                                ))}
                            </select>
                        </label>
                    </div>
                    {(!selectedStudentId || !selectedSubjectId || !selectedTermId) && (
                        <p style={{ marginTop: '0.75rem', color: 'var(--text-secondary)' }}>
                            Selecciona asignatura, trimestre y alumno para ver métricas, recomendaciones e informes.
                        </p>
                    )}
                </div>
            )}

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
            </div>

            {/* Content */}
            {activeTab === 'content' && (
                <div style={{ display: 'grid', gap: '2rem' }}>
                    <section>
                        <UploadForm tutorId={tutorId} subjectId={selectedSubjectId} termId={selectedTermId} />
                    </section>
                    <section>
                        <UploadList tutorId={tutorId} />
                    </section>
                </div>
            )}

            {activeTab === 'metrics' && (
                selectedStudentId && selectedSubjectId && selectedTermId ? (
                    <MetricsDashboard
                        studentId={selectedStudentId}
                        subjectId={selectedSubjectId}
                        termId={selectedTermId}
                    />
                ) : (
                    <p>Selecciona contexto para ver métricas.</p>
                )
            )}

            {activeTab === 'recommendations' && (
                selectedStudentId && selectedSubjectId && selectedTermId && tutorId ? (
                    <RecommendationList
                        studentId={selectedStudentId}
                        subjectId={selectedSubjectId}
                        termId={selectedTermId}
                        tutorId={tutorId}
                    />
                ) : (
                    <p>Selecciona contexto para ver recomendaciones.</p>
                )
            )}

            {activeTab === 'reports' && (
                selectedStudentId && selectedSubjectId && selectedTermId && tutorId ? (
                    <TutorReportPanel
                        tutorId={tutorId}
                        studentId={selectedStudentId}
                        subjectId={selectedSubjectId}
                        termId={selectedTermId}
                    />
                ) : (
                    <p>Selecciona contexto para ver informes.</p>
                )
            )}
        </div>
    );
}
