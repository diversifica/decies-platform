"use client";

import { useEffect, useState } from 'react';
import api from '../../services/api';

interface StudentMetrics {
    student_id: string;
    subject_id: string;
    term_id: string;
    accuracy: number | null;
    first_attempt_accuracy: number | null;
    median_response_time_ms: number | null;
    hint_rate: number | null;
    total_sessions: number;
    total_items_completed: number;
    window_start: string;
    window_end: string;
}

interface MasteryState {
    microconcept_id: string;
    microconcept_name: string;
    mastery_score: number;
    status: string;
    last_practice_at: string | null;
    total_events: number;
}

interface MetricsDashboardProps {
    studentId: string;
    subjectId: string;
    termId: string;
}

export default function MetricsDashboard({ studentId, subjectId, termId }: MetricsDashboardProps) {
    const [metrics, setMetrics] = useState<StudentMetrics | null>(null);
    const [masteryStates, setMasteryStates] = useState<MasteryState[]>([]);
    const [loading, setLoading] = useState(true);
    const [bootstrapLoading, setBootstrapLoading] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const metricsRes = await api.get(`/metrics/students/${studentId}/metrics`, {
                    params: { subject_id: subjectId, term_id: termId }
                });
                setMetrics(metricsRes.data);

                const masteryRes = await api.get(`/metrics/students/${studentId}/mastery`, {
                    params: { subject_id: subjectId, term_id: termId }
                });
                setMasteryStates(masteryRes.data);
            } catch (err: any) {
                console.error('Error fetching metrics:', err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [studentId, subjectId, termId]);

    if (loading) return <p>Cargando métricas...</p>;
    if (!metrics) return <p>No hay datos de métricas disponibles.</p>;

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'dominant': return 'var(--success)';
            case 'in_progress': return 'var(--warning)';
            case 'at_risk': return 'var(--error)';
            default: return 'var(--text-secondary)';
        }
    };

    const getStatusLabel = (status: string) => {
        switch (status) {
            case 'dominant': return 'Dominado';
            case 'in_progress': return 'En Progreso';
            case 'at_risk': return 'En Riesgo';
            default: return status;
        }
    };

    const formatPercentage = (value: number | null) => {
        if (value === null) return 'N/A';
        return `${(value * 100).toFixed(1)}%`;
    };

    const formatTime = (ms: number | null) => {
        if (ms === null) return 'N/A';
        if (ms < 1000) return `${ms}ms`;
        return `${(ms / 1000).toFixed(1)}s`;
    };

    const bootstrapDomain = async () => {
        setBootstrapLoading(true);
        try {
            await api.post('/microconcepts/bootstrap', null, {
                params: { subject_id: subjectId, term_id: termId }
            });

            const masteryRes = await api.get(`/metrics/students/${studentId}/mastery`, {
                params: { subject_id: subjectId, term_id: termId }
            });
            setMasteryStates(masteryRes.data);
        } catch (err: any) {
            console.error('Error bootstrapping domain:', err);
            alert(err?.response?.data?.detail || err?.message || 'Error inicializando dominio');
        } finally {
            setBootstrapLoading(false);
        }
    };

    return (
        <div>
            <h2 style={{ marginBottom: '2rem' }}>Dashboard de Métricas</h2>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
                <div className="card" style={{ textAlign: 'center' }}>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Precisión Global</p>
                    <p style={{ fontSize: '2rem', fontWeight: 'bold', color: 'var(--primary)' }}>
                        {formatPercentage(metrics.accuracy)}
                    </p>
                </div>

                <div className="card" style={{ textAlign: 'center' }}>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Primer Intento</p>
                    <p style={{ fontSize: '2rem', fontWeight: 'bold', color: 'var(--success)' }}>
                        {formatPercentage(metrics.first_attempt_accuracy)}
                    </p>
                </div>

                <div className="card" style={{ textAlign: 'center' }}>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Tiempo Mediano</p>
                    <p style={{ fontSize: '2rem', fontWeight: 'bold', color: 'var(--accent)' }}>
                        {formatTime(metrics.median_response_time_ms)}
                    </p>
                </div>

                <div className="card" style={{ textAlign: 'center' }}>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Sesiones</p>
                    <p style={{ fontSize: '2rem', fontWeight: 'bold' }}>
                        {metrics.total_sessions}
                    </p>
                </div>

                <div className="card" style={{ textAlign: 'center' }}>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Items Completados</p>
                    <p style={{ fontSize: '2rem', fontWeight: 'bold' }}>
                        {metrics.total_items_completed}
                    </p>
                </div>

                <div className="card" style={{ textAlign: 'center' }}>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Uso de Ayudas</p>
                    <p style={{ fontSize: '2rem', fontWeight: 'bold', color: 'var(--warning)' }}>
                        {formatPercentage(metrics.hint_rate)}
                    </p>
                </div>
            </div>

            <div className="card">
                <h3 style={{ marginBottom: '1.5rem' }}>Estado de Dominio por Microconcepto</h3>

                {masteryStates.length === 0 ? (
                    <div style={{ display: 'grid', gap: '1rem' }}>
                        <p style={{ color: 'var(--text-secondary)', margin: 0 }}>
                            No hay datos de dominio disponibles aún.
                        </p>
                        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
                            <button
                                onClick={bootstrapDomain}
                                className="btn"
                                disabled={bootstrapLoading}
                            >
                                {bootstrapLoading ? 'Inicializando...' : 'Inicializar dominio (dev)'}
                            </button>
                            <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                                Crea un microconcepto &quot;General&quot; para este subject/term y alinea items/eventos.
                            </span>
                        </div>
                    </div>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        {masteryStates.map((ms) => (
                            <div
                                key={ms.microconcept_id}
                                style={{
                                    padding: '1rem',
                                    backgroundColor: 'var(--bg-primary)',
                                    borderRadius: 'var(--radius-md)',
                                    borderLeft: `4px solid ${getStatusColor(ms.status)}`
                                }}
                            >
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                                    <h4 style={{ margin: 0 }}>{ms.microconcept_name}</h4>
                                    <span
                                        style={{
                                            padding: '0.25rem 0.75rem',
                                            borderRadius: 'var(--radius-sm)',
                                            backgroundColor: getStatusColor(ms.status),
                                            color: 'white',
                                            fontSize: '0.875rem',
                                            fontWeight: 'bold'
                                        }}
                                    >
                                        {getStatusLabel(ms.status)}
                                    </span>
                                </div>

                                <div style={{ display: 'flex', gap: '2rem', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                                    <div>
                                        <strong>Score de Dominio:</strong> {(ms.mastery_score * 100).toFixed(1)}%
                                    </div>
                                    <div>
                                        <strong>Eventos:</strong> {ms.total_events}
                                    </div>
                                    {ms.last_practice_at && (
                                        <div>
                                            <strong>Última Práctica:</strong> {new Date(ms.last_practice_at).toLocaleDateString()}
                                        </div>
                                    )}
                                </div>

                                <div style={{ marginTop: '0.75rem', height: '8px', backgroundColor: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', overflow: 'hidden' }}>
                                    <div
                                        style={{
                                            height: '100%',
                                            width: `${ms.mastery_score * 100}%`,
                                            backgroundColor: getStatusColor(ms.status),
                                            transition: 'width 0.3s ease'
                                        }}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            <p style={{ marginTop: '2rem', fontSize: '0.875rem', color: 'var(--text-secondary)', textAlign: 'center' }}>
                Datos de los últimos 30 días — Actualizado automáticamente tras cada sesión
            </p>
        </div>
    );
}
