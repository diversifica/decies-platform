import { useMemo, useState } from 'react';
import api from '../../services/api';

interface Evidence {
    id: string;
    evidence_type: string;
    key: string;
    value: string;
    description: string;
}

interface Recommendation {
    id: string;
    title: string;
    description: string;
    priority: 'high' | 'medium' | 'low';
    status: 'pending' | 'accepted' | 'rejected';
    rule_id: string;
    category?: string | null;
    generated_at: string;
    evidence: Evidence[];
    outcome?: {
        id: string;
        recommendation_id: string;
        evaluation_start: string;
        evaluation_end: string;
        success: string; // true/false/partial
        delta_mastery?: number | null;
        delta_accuracy?: number | null;
        delta_hint_rate?: number | null;
        computed_at: string;
        notes?: string | null;
    } | null;
}

interface RecommendationCardProps {
    recommendation: Recommendation;
    tutorId: string;
    onDecisionMade: (id: string, decision: 'accepted' | 'rejected') => void;
}

export default function RecommendationCard({ recommendation, tutorId, onDecisionMade }: RecommendationCardProps) {
    const [loading, setLoading] = useState(false);

    const categoryLabel = (category: string | null | undefined) => {
        switch ((category || '').toLowerCase()) {
            case 'focus': return 'Focus';
            case 'strategy': return 'Estrategia';
            case 'dosage': return 'Dosificación';
            case 'external_validation': return 'Validación externa';
            default: return null;
        }
    };

    const handleDecision = async (decision: 'accepted' | 'rejected') => {
        setLoading(true);
        try {
            await api.post(`/recommendations/${recommendation.id}/decision`, {
                recommendation_id: recommendation.id,
                decision,
                tutor_id: tutorId,
                notes: `Tutor decision: ${decision}`
            });
            onDecisionMade(recommendation.id, decision);
        } catch (error) {
            console.error('Error recording decision:', error);
            alert('Error al registrar la decisión');
        } finally {
            setLoading(false);
        }
    };

    const getPriorityColor = (priority: string) => {
        switch (priority) {
            case 'high': return 'var(--error)';
            case 'medium': return 'var(--warning)';
            case 'low': return 'var(--success)'; // or neutral
            default: return 'var(--text-secondary)';
        }
    };

    const outcomeBadge = useMemo(() => {
        const outcome = recommendation.outcome;
        if (!outcome) return null;

        const success = (outcome.success || '').toLowerCase();
        if (success === 'true') return { label: 'Éxito', color: 'var(--success)' };
        if (success === 'false') return { label: 'Sin efecto', color: 'var(--error)' };
        return { label: 'Parcial', color: 'var(--warning)' };
    }, [recommendation.outcome]);

    const formatDelta = (value: number | null | undefined, unit: 'pp' | 'score') => {
        if (value == null || Number.isNaN(value)) return 'N/A';
        const sign = value > 0 ? '+' : '';
        if (unit === 'pp') return `${sign}${(value * 100).toFixed(1)}pp`;
        return `${sign}${value.toFixed(3)}`;
    };

    return (
        <div className="card" style={{ borderLeft: `4px solid ${getPriorityColor(recommendation.priority)}` }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '0.5rem' }}>
                        <span className="badge" style={{ backgroundColor: getPriorityColor(recommendation.priority) }}>
                            {recommendation.priority.toUpperCase()}
                        </span>
                        <span className="badge" style={{ backgroundColor: 'var(--bg-secondary)', color: 'var(--text-primary)', border: '1px solid var(--border-color)' }}>
                            {recommendation.rule_id}
                        </span>
                        {categoryLabel(recommendation.category) && (
                            <span className="badge" style={{ backgroundColor: 'var(--bg-secondary)', color: 'var(--text-secondary)', border: '1px solid var(--border-color)' }}>
                                {categoryLabel(recommendation.category)}
                            </span>
                        )}
                    </div>
                    <h3 style={{ margin: '0.5rem 0' }}>{recommendation.title}</h3>
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    {new Date(recommendation.generated_at).toLocaleDateString()}
                </div>
            </div>

            <p style={{ margin: '1rem 0' }}>{recommendation.description}</p>

            {recommendation.status === 'accepted' && (
                <div
                    style={{
                        backgroundColor: 'var(--bg-secondary)',
                        padding: '0.8rem',
                        borderRadius: 'var(--radius-sm)',
                        marginBottom: '1rem',
                    }}
                >
                    <div
                        style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            gap: '1rem',
                            alignItems: 'center',
                        }}
                    >
                        <h4 style={{ fontSize: '0.9rem', margin: 0 }}>Impacto</h4>
                        {outcomeBadge && (
                            <span className="badge" style={{ backgroundColor: outcomeBadge.color }}>
                                {outcomeBadge.label}
                            </span>
                        )}
                    </div>

                    {recommendation.outcome ? (
                        <div style={{ marginTop: '0.6rem', display: 'grid', gap: '0.35rem', fontSize: '0.9rem' }}>
                            <div style={{ color: 'var(--text-secondary)' }}>
                                Ventana: {new Date(recommendation.outcome.evaluation_start).toLocaleDateString()} —{' '}
                                {new Date(recommendation.outcome.evaluation_end).toLocaleDateString()}
                            </div>
                            <div>
                                Δ Accuracy: <strong>{formatDelta(recommendation.outcome.delta_accuracy, 'pp')}</strong>
                                {' · '}
                                Δ Mastery: <strong>{formatDelta(recommendation.outcome.delta_mastery, 'score')}</strong>
                                {' · '}
                                Δ Hint: <strong>{formatDelta(recommendation.outcome.delta_hint_rate, 'pp')}</strong>
                            </div>
                        </div>
                    ) : (
                        <p style={{ margin: '0.6rem 0 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                            Aún no hay impacto calculado para esta recomendación.
                        </p>
                    )}
                </div>
            )}

            {recommendation.evidence.length > 0 && (
                <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '0.8rem', borderRadius: 'var(--radius-sm)', marginBottom: '1rem' }}>
                    <h4 style={{ fontSize: '0.9rem', marginBottom: '0.5rem' }}>Evidencia Detectada:</h4>
                    <ul style={{ margin: 0, paddingLeft: '1.2rem', fontSize: '0.9rem' }}>
                        {recommendation.evidence.map(ev => (
                            <li key={ev.id}>
                                <strong>{ev.description || ev.key}:</strong> {ev.value}
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {recommendation.status === 'pending' ? (
                <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                    <button
                        onClick={() => handleDecision('accepted')}
                        disabled={loading}
                        className="btn"
                        style={{ backgroundColor: 'var(--success)', flex: 1 }}
                    >
                        {loading ? '...' : 'Aceptar Sugerencia'}
                    </button>
                    <button
                        onClick={() => handleDecision('rejected')}
                        disabled={loading}
                        className="btn"
                        style={{ backgroundColor: 'var(--bg-secondary)', color: 'var(--text-primary)', border: '1px solid var(--border-color)', flex: 1 }}
                    >
                        {loading ? '...' : 'Rechazar'}
                    </button>
                </div>
            ) : (
                <div style={{ marginTop: '1rem', padding: '0.5rem', textAlign: 'center', backgroundColor: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)' }}>
                    Estado: <strong>{recommendation.status === 'accepted' ? 'Aceptada' : 'Rechazada'}</strong>
                </div>
            )}
        </div>
    );
}
