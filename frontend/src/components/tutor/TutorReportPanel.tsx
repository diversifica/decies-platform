"use client";

import { useEffect, useState } from 'react';
import api from '../../services/api';

interface TutorReportSection {
  id: string;
  report_id: string;
  order_index: number;
  section_type: string;
  title: string;
  content: string;
  data?: any;
}

interface TutorReport {
  id: string;
  tutor_id: string;
  student_id: string;
  subject_id: string;
  term_id: string;
  summary: string;
  generated_at: string;
  sections: TutorReportSection[];
}

interface TutorReportPanelProps {
    tutorId: string;
    studentId: string;
    subjectId: string;
    termId: string;
}

export default function TutorReportPanel({ tutorId, studentId, subjectId, termId }: TutorReportPanelProps) {
    const [report, setReport] = useState<TutorReport | null>(null);
    const [loading, setLoading] = useState(true);
    const [generating, setGenerating] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchLatest = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await api.get(`/reports/students/${studentId}/latest`, {
                params: { tutor_id: tutorId, subject_id: subjectId, term_id: termId },
            });
            setReport(res.data);
        } catch (err: any) {
            if (err?.response?.status === 404) {
                setReport(null);
            } else {
                setError(err?.response?.data?.detail || err.message || 'Error cargando informe');
            }
        } finally {
            setLoading(false);
        }
    };

    const generate = async () => {
        setGenerating(true);
        setError(null);
        try {
            const res = await api.post(`/reports/students/${studentId}/generate`, null, {
                params: { tutor_id: tutorId, subject_id: subjectId, term_id: termId, generate_recommendations: true },
            });
            setReport(res.data);
        } catch (err: any) {
            setError(err?.response?.data?.detail || err.message || 'Error generando informe');
        } finally {
            setGenerating(false);
        }
    };

    useEffect(() => {
        fetchLatest();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [tutorId, studentId, subjectId, termId]);

    if (loading) return <p>Cargando informe...</p>;

    return (
        <div className="card" style={{ padding: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem' }}>
                <div>
                    <h3 style={{ margin: 0 }}>Informe del alumno</h3>
                    <p style={{ margin: '0.25rem 0 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                        {report ? `Última generación: ${new Date(report.generated_at).toLocaleString()}` : 'Aún no hay informes.'}
                    </p>
                </div>
                <div style={{ display: 'flex', gap: '0.75rem' }}>
                    <button onClick={fetchLatest} className="btn btn-secondary" disabled={generating}>
                        Refrescar
                    </button>
                    <button onClick={generate} className="btn" disabled={generating}>
                        {generating ? 'Generando...' : 'Generar informe'}
                    </button>
                </div>
            </div>

            {error && <p style={{ marginTop: '1rem', color: 'var(--error)' }}>{error}</p>}

            {!report ? (
                <p style={{ marginTop: '1rem', color: 'var(--text-secondary)' }}>
                    Genera un informe para ver resumen, estado de dominio y recomendaciones activas.
                </p>
            ) : (
                <div style={{ marginTop: '1.25rem', display: 'grid', gap: '1rem' }}>
                    <div style={{ background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', padding: '1rem' }}>
                        <h4 style={{ marginTop: 0 }}>Resumen</h4>
                        <pre style={{ whiteSpace: 'pre-wrap', margin: 0, fontFamily: 'inherit' }}>{report.summary}</pre>
                    </div>

                    {report.sections
                        .slice()
                        .sort((a, b) => a.order_index - b.order_index)
                        .map((section) => (
                            <div
                                key={section.id}
                                style={{ background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', padding: '1rem' }}
                            >
                                <h4 style={{ marginTop: 0 }}>{section.title}</h4>
                                {section.section_type === 'real_grades' && Array.isArray(section.data?.recent) ? (
                                    <div style={{ display: 'grid', gap: '0.75rem' }}>
                                        {section.data?.stats && (
                                            <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                                                Tendencia: {section.data?.stats?.trend || 'N/A'} · Media recientes: {section.data?.stats?.average_recent || 'N/A'}
                                            </p>
                                        )}
                                        {section.data.recent.length === 0 ? (
                                            <p style={{ margin: 0, color: 'var(--text-secondary)' }}>{section.content}</p>
                                        ) : (
                                            <div style={{ overflowX: 'auto' }}>
                                                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                                    <thead>
                                                        <tr style={{ textAlign: 'left', color: 'var(--text-secondary)' }}>
                                                            <th style={{ padding: '0.5rem' }}>Fecha</th>
                                                            <th style={{ padding: '0.5rem' }}>Nota</th>
                                                            <th style={{ padding: '0.5rem' }}>Escala</th>
                                                            <th style={{ padding: '0.5rem' }}>Notas</th>
                                                            <th style={{ padding: '0.5rem' }}>Tags</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {section.data.recent.map((g: any) => (
                                                            <tr key={g.id} style={{ borderTop: '1px solid var(--border-color)' }}>
                                                                <td style={{ padding: '0.5rem' }}>{g.assessment_date}</td>
                                                                <td style={{ padding: '0.5rem' }}>{g.grade_value ?? 'N/A'}</td>
                                                                <td style={{ padding: '0.5rem' }}>{g.grading_scale || '-'}</td>
                                                                <td style={{ padding: '0.5rem' }}>{g.notes || '-'}</td>
                                                                <td style={{ padding: '0.5rem' }}>
                                                                    {Array.isArray(g.tags) && g.tags.length ? g.tags.join(' | ') : '-'}
                                                                </td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            </div>
                                        )}
                                    </div>
                                ) : (
                                    <pre style={{ whiteSpace: 'pre-wrap', margin: 0, fontFamily: 'inherit' }}>{section.content}</pre>
                                )}
                            </div>
                        ))}
                </div>
            )}
        </div>
    );
}
