import { useState } from 'react';
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
    generated_at: string;
    evidence: Evidence[];
}

interface RecommendationCardProps {
    recommendation: Recommendation;
    tutorId: string;
    onDecisionMade: (id: string, decision: 'accepted' | 'rejected') => void;
}

export default function RecommendationCard({ recommendation, tutorId, onDecisionMade }: RecommendationCardProps) {
    const [loading, setLoading] = useState(false);

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

    return (
        <div className="card" style={{ borderLeft: `4px solid ${getPriorityColor(recommendation.priority)}` }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <span className="badge" style={{ backgroundColor: getPriorityColor(recommendation.priority), marginBottom: '0.5rem' }}>
                        {recommendation.priority.toUpperCase()}
                    </span>
                    <h3 style={{ margin: '0.5rem 0' }}>{recommendation.title}</h3>
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    {new Date(recommendation.generated_at).toLocaleDateString()}
                </div>
            </div>

            <p style={{ margin: '1rem 0' }}>{recommendation.description}</p>

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
