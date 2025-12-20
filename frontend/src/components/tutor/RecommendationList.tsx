import { useCallback, useEffect, useState } from 'react';
import api from '../../services/api';
import RecommendationCard from './RecommendationCard';

type SortKey = 'newest' | 'priority' | 'category';

interface RecommendationListProps {
    studentId: string;
    subjectId: string;
    termId: string;
    tutorId: string; // Current tutor ID
}

export default function RecommendationList({ studentId, subjectId, termId, tutorId }: RecommendationListProps) {
    const [recommendations, setRecommendations] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('pending'); // pending, all, accepted, rejected
    const [categoryFilter, setCategoryFilter] = useState<string>('all');
    const [sortKey, setSortKey] = useState<SortKey>('priority');
    const [computingOutcomes, setComputingOutcomes] = useState(false);
    const [outcomeMessage, setOutcomeMessage] = useState<string | null>(null);

    const fetchRecommendations = useCallback(async () => {
        setLoading(true);
        try {
            // Generate is true by default in API, which is what we want on first load/refresh
            const response = await api.get(`/recommendations/students/${studentId}`, {
                params: {
                    subject_id: subjectId,
                    term_id: termId,
                    status_filter: filter
                }
            });
            setRecommendations(response.data);
        } catch (error) {
            console.error('Error fetching recommendations:', error);
        } finally {
            setLoading(false);
        }
    }, [studentId, subjectId, termId, filter]);

    useEffect(() => {
        fetchRecommendations();
    }, [fetchRecommendations]);

    const getPriorityRank = (priority: string) => {
        switch ((priority || '').toLowerCase()) {
            case 'high': return 0;
            case 'medium': return 1;
            case 'low': return 2;
            default: return 3;
        }
    };

    const getCategoryRank = (category: string) => {
        switch ((category || '').toLowerCase()) {
            case 'focus': return 0;
            case 'strategy': return 1;
            case 'dosage': return 2;
            case 'external_validation': return 3;
            default: return 4;
        }
    };

    const visibleRecommendations = recommendations
        .filter(rec => categoryFilter === 'all' || (rec.category || '').toLowerCase() === categoryFilter)
        .slice()
        .sort((a, b) => {
            if (sortKey === 'newest') {
                return new Date(b.generated_at).getTime() - new Date(a.generated_at).getTime();
            }
            if (sortKey === 'category') {
                const c = getCategoryRank(a.category) - getCategoryRank(b.category);
                if (c !== 0) return c;
                const p = getPriorityRank(a.priority) - getPriorityRank(b.priority);
                if (p !== 0) return p;
                return new Date(b.generated_at).getTime() - new Date(a.generated_at).getTime();
            }

            const p = getPriorityRank(a.priority) - getPriorityRank(b.priority);
            if (p !== 0) return p;
            return new Date(b.generated_at).getTime() - new Date(a.generated_at).getTime();
        });

    const computeOutcomes = async (force = false) => {
        setComputingOutcomes(true);
        setOutcomeMessage(null);
        try {
            const res = await api.post('/recommendations/outcomes/compute', null, {
                params: {
                    student_id: studentId,
                    subject_id: subjectId,
                    term_id: termId,
                    force,
                },
            });
            const { created, updated, pending } = res.data || {};
            setOutcomeMessage(
                `Impacto actualizado: +${created || 0} creados, ~${updated || 0} actualizados (pendientes: ${pending || 0}).`
            );
            await fetchRecommendations();
        } catch (error: any) {
            const detail = error?.response?.data?.detail || error?.message || 'Error calculando impacto';
            setOutcomeMessage(detail);
        } finally {
            setComputingOutcomes(false);
        }
    };

    const handleDecisionMade = (id: string, decision: 'accepted' | 'rejected') => {
        // Optimistic update
        setRecommendations(prev => prev.map(rec => {
            if (rec.id === id) {
                return { ...rec, status: decision === 'accepted' ? 'accepted' : 'rejected' };
            }
            return rec;
        }));

        // If filtering by pending, remove it after delay
        if (filter === 'pending') {
            setTimeout(() => {
                setRecommendations(prev => prev.filter(rec => rec.id !== id));
            }, 1000);
        }
    };

    return (
        <div style={{ padding: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h2>Recomendaciones de Estudio</h2>
                <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                    <button
                        className="btn btn-secondary"
                        onClick={() => computeOutcomes(false)}
                        disabled={computingOutcomes}
                        title="Calcula el impacto de recomendaciones aceptadas (si hay sesiones suficientes)"
                    >
                        {computingOutcomes ? 'Calculando...' : 'Actualizar impacto'}
                    </button>
                    <button
                        className="btn btn-secondary"
                        onClick={() => computeOutcomes(true)}
                        disabled={computingOutcomes}
                        title="Recalcula el impacto aunque ya exista un outcome guardado"
                    >
                        Forzar
                    </button>
                    <select
                        value={categoryFilter}
                        onChange={(e) => setCategoryFilter(e.target.value)}
                        className="input"
                        style={{ width: 'auto' }}
                        title="Filtrar por categoría"
                    >
                        <option value="all">Todas las categorías</option>
                        <option value="focus">Focus</option>
                        <option value="strategy">Estrategia</option>
                        <option value="dosage">Dosificación</option>
                        <option value="external_validation">Validación externa</option>
                    </select>
                    <select
                        value={sortKey}
                        onChange={(e) => setSortKey(e.target.value as SortKey)}
                        className="input"
                        style={{ width: 'auto' }}
                        title="Ordenar recomendaciones"
                    >
                        <option value="priority">Ordenar por prioridad</option>
                        <option value="category">Ordenar por categoría</option>
                        <option value="newest">Más recientes</option>
                    </select>
                    <select
                        value={filter}
                        onChange={(e) => setFilter(e.target.value)}
                        className="input"
                        style={{ width: 'auto' }}
                    >
                        <option value="pending">Pendientes</option>
                        <option value="accepted">Aceptadas</option>
                        <option value="rejected">Rechazadas</option>
                        <option value="all">Todas</option>
                    </select>
                </div>
            </div>

            {outcomeMessage && (
                <p style={{ margin: '-0.75rem 0 1.25rem', color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
                    {outcomeMessage}
                </p>
            )}

            {loading ? (
                <p>Analizando rendimiento...</p>
            ) : recommendations.length === 0 ? (
                <div style={{ padding: '2rem', textAlign: 'center', backgroundColor: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)' }}>
                    <p>No hay recomendaciones {filter === 'pending' ? 'pendientes' : 'disponibles'} en este momento.</p>
                    <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>El sistema genera sugerencias basadas en la actividad reciente del alumno.</p>
                </div>
            ) : visibleRecommendations.length === 0 ? (
                <div style={{ padding: '2rem', textAlign: 'center', backgroundColor: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)' }}>
                    <p>No hay recomendaciones que coincidan con los filtros actuales.</p>
                    <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Prueba a cambiar la categoría o el estado.</p>
                </div>
            ) : (
                <div style={{ display: 'grid', gap: '1.5rem', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))' }}>
                    {visibleRecommendations.map(rec => (
                        <RecommendationCard
                            key={rec.id}
                            recommendation={rec}
                            tutorId={tutorId}
                            onDecisionMade={handleDecisionMade}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}
