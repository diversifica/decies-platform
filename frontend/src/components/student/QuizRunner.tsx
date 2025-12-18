"use client";

import { useEffect, useState } from 'react';
import api from '../../services/api';

interface Item {
    id: string;
    type: string;
    stem: string;
    options?: any;
    correct_answer: string;
    explanation?: string;
}

interface QuizRunnerProps {
    uploadId: string;
    studentId: string;
    subjectId: string;
    termId: string;
    onExit: () => void;
}

export default function QuizRunner({ uploadId, studentId, subjectId, termId, onExit }: QuizRunnerProps) {
    const [items, setItems] = useState<Item[]>([]);
    const [loading, setLoading] = useState(true);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [activityTypeId, setActivityTypeId] = useState<string | null>(null);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [score, setScore] = useState(0);
    const [finished, setFinished] = useState(false);
    const [selectedOption, setSelectedOption] = useState<string | null>(null);
    const [feedback, setFeedback] = useState<{ isCorrect: boolean, text: string } | null>(null);
    const [questionStartTime, setQuestionStartTime] = useState<Date>(new Date());
    const [sessionFeedbackRating, setSessionFeedbackRating] = useState<number>(5);
    const [sessionFeedbackText, setSessionFeedbackText] = useState<string>('');
    const [sessionFeedbackSubmitting, setSessionFeedbackSubmitting] = useState(false);
    const [sessionFeedbackSubmitted, setSessionFeedbackSubmitted] = useState(false);
    const [sessionFeedbackError, setSessionFeedbackError] = useState<string>('');

    useEffect(() => {
        const initSession = async () => {
            try {
                // 1. Get QUIZ activity type
                const typesRes = await api.get('/activities/activity-types');
                const quizType = typesRes.data.find((t: any) => t.code === 'QUIZ');
                if (!quizType) {
                    console.error('QUIZ activity type not found');
                    setLoading(false);
                    return;
                }
                setActivityTypeId(quizType.id);

                // 2. Create activity session
                const sessionRes = await api.post('/activities/sessions', {
                    student_id: studentId,
                    activity_type_id: quizType.id,
                    subject_id: subjectId,
                    term_id: termId,
                    topic_id: null,
                    item_count: 10,
                    content_upload_id: uploadId,
                    device_type: 'web'
                });
                setSessionId(sessionRes.data.id);

                // 3. Get session items (ordered)
                const sessionItemsRes = await api.get(`/activities/sessions/${sessionRes.data.id}/items`);
                setItems(sessionItemsRes.data);
                setQuestionStartTime(new Date());

            } catch (err: any) {
                console.error('Error initializing session:', err);
            } finally {
                setLoading(false);
            }
        };
        initSession();
    }, [uploadId, studentId, subjectId, termId]);

    if (loading) return <p>Cargando preguntas...</p>;
    if (items.length === 0) return <p>No hay preguntas disponibles para este contenido.</p>;
    if (!sessionId || !activityTypeId) return <p>Error al iniciar la sesión.</p>;

    const currentItem = items[currentIndex];
    const options: string[] = Array.isArray(currentItem.options)
        ? currentItem.options
        : (Array.isArray(currentItem.options?.choices) ? currentItem.options.choices : []);

    const handleAnswer = async (option: string) => {
        if (selectedOption) return; // Prevent double answer
        setSelectedOption(option);

        const endTime = new Date();
        const durationMs = endTime.getTime() - questionStartTime.getTime();

        // Check answer
        const isCorrect = option === currentItem.correct_answer;

        if (isCorrect) {
            setScore(s => s + 1);
            setFeedback({ isCorrect: true, text: "¡Correcto!" });
        } else {
            setFeedback({
                isCorrect: false,
                text: `Incorrecto. La respuesta correcta es: ${currentItem.correct_answer}. ${currentItem.explanation || ''}`
            });
        }

        // Record learning event
        try {
            await api.post(`/activities/sessions/${sessionId}/responses`, {
                student_id: studentId,
                item_id: currentItem.id,
                subject_id: subjectId,
                term_id: termId,
                topic_id: null,
                microconcept_id: null, // Will be derived from item
                activity_type_id: activityTypeId,
                is_correct: isCorrect,
                duration_ms: durationMs,
                attempt_number: 1,
                response_normalized: option,
                hint_used: null,
                difficulty_at_time: null,
                timestamp_start: questionStartTime.toISOString(),
                timestamp_end: endTime.toISOString()
            });
        } catch (err: any) {
            console.error('Error recording event:', err);
        }
    };

    const nextQuestion = () => {
        setSelectedOption(null);
        setFeedback(null);
        setQuestionStartTime(new Date()); // Reset timer for next question

        if (currentIndex < items.length - 1) {
            setCurrentIndex(i => i + 1);
        } else {
            finishSession();
        }
    };

    const finishSession = async () => {
        try {
            await api.post(`/activities/sessions/${sessionId}/end`);
        } catch (err: any) {
            console.error('Error ending session:', err);
        }
        setFinished(true);
    };

    const submitSessionFeedback = async () => {
        if (!sessionId || sessionFeedbackSubmitted) return;
        setSessionFeedbackSubmitting(true);
        setSessionFeedbackError('');
        try {
            await api.post(`/activities/sessions/${sessionId}/feedback`, {
                rating: sessionFeedbackRating,
                text: sessionFeedbackText || null,
            });
            setSessionFeedbackSubmitted(true);
        } catch (err: any) {
            setSessionFeedbackError(err?.response?.data?.detail || err?.message || 'Error enviando feedback');
        } finally {
            setSessionFeedbackSubmitting(false);
        }
    };

    if (finished) {
        return (
            <div className="card" style={{ textAlign: 'center' }}>
                <h3>Actividad Completada</h3>
                <p style={{ fontSize: '2rem', margin: '2rem 0' }}>Score: {score} / {items.length}</p>
                <p style={{ color: 'var(--text-secondary)' }}>
                    Tus métricas se han actualizado automáticamente.
                </p>

                <div style={{ marginTop: '1.5rem', textAlign: 'left' }}>
                    <h4 style={{ marginTop: 0 }}>Feedback (opcional)</h4>
                    <label style={{ display: 'block', marginBottom: '0.75rem' }}>
                        Valoración
                        <select
                            className="input"
                            value={sessionFeedbackRating}
                            onChange={(e) => setSessionFeedbackRating(Number(e.target.value))}
                            disabled={sessionFeedbackSubmitting || sessionFeedbackSubmitted}
                        >
                            {[1, 2, 3, 4, 5].map((v) => (
                                <option key={v} value={v}>{v}</option>
                            ))}
                        </select>
                    </label>
                    <label style={{ display: 'block' }}>
                        Comentario
                        <textarea
                            className="input"
                            rows={3}
                            value={sessionFeedbackText}
                            onChange={(e) => setSessionFeedbackText(e.target.value)}
                            disabled={sessionFeedbackSubmitting || sessionFeedbackSubmitted}
                            placeholder="¿Qué te ha parecido la sesión?"
                        />
                    </label>
                    {sessionFeedbackError && (
                        <p style={{ color: 'var(--error)', marginTop: '0.75rem' }}>{sessionFeedbackError}</p>
                    )}
                    {sessionFeedbackSubmitted && (
                        <p style={{ color: 'var(--success)', marginTop: '0.75rem' }}>Feedback enviado.</p>
                    )}
                    <button
                        onClick={submitSessionFeedback}
                        className="btn btn-secondary"
                        disabled={sessionFeedbackSubmitting || sessionFeedbackSubmitted}
                        style={{ marginTop: '0.75rem' }}
                    >
                        {sessionFeedbackSubmitting ? 'Enviando...' : 'Enviar feedback'}
                    </button>
                </div>
                <button onClick={onExit} className="btn">Volver al inicio</button>
            </div>
        );
    }

    return (
        <div className="card" style={{ maxWidth: '600px', margin: '0 auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem', color: 'var(--text-secondary)' }}>
                <span>Pregunta {currentIndex + 1} de {items.length}</span>
                <span>Score: {score}</span>
            </div>

            <h3 style={{ marginBottom: '1.5rem' }}>{currentItem.stem}</h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {options.length > 0 ? (
                    options.map((opt, idx) => (
                        <button
                            key={idx}
                            onClick={() => handleAnswer(opt)}
                            className="input"
                            style={{
                                textAlign: 'left',
                                cursor: selectedOption ? 'default' : 'pointer',
                                backgroundColor: selectedOption === opt
                                    ? (feedback?.isCorrect ? 'var(--success)' : 'var(--error)')
                                    : (selectedOption && opt === currentItem.correct_answer ? 'var(--success)' : 'var(--bg-primary)'),
                                color: selectedOption ? 'white' : 'var(--text-primary)',
                                border: selectedOption === opt ? 'none' : '1px solid var(--border-color)'
                            }}
                            disabled={!!selectedOption}
                        >
                            {opt}
                        </button>
                    ))
                ) : (
                    <p>Error: No options provided for question.</p>
                )}
            </div>

            {feedback && (
                <div style={{ marginTop: '2rem', padding: '1rem', backgroundColor: 'var(--bg-primary)', borderRadius: 'var(--radius-md)' }}>
                    <p style={{ color: feedback.isCorrect ? 'var(--success)' : 'var(--error)', fontWeight: 'bold' }}>
                        {feedback.text}
                    </p>
                    <button onClick={nextQuestion} className="btn" style={{ marginTop: '1rem' }}>Siguiente</button>
                </div>
            )}
        </div>
    );
}
