"use client";

import { useCallback, useEffect, useState } from 'react';
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
    activityCode?: 'QUIZ' | 'EXAM_STYLE';
    examMode?: boolean;
    timeLimitSeconds?: number;
    itemCount?: number;
}

export default function QuizRunner({
    uploadId,
    studentId,
    subjectId,
    termId,
    onExit,
    activityCode = 'QUIZ',
    examMode = false,
    timeLimitSeconds,
    itemCount = 10,
}: QuizRunnerProps) {
    const [items, setItems] = useState<Item[]>([]);
    const [loading, setLoading] = useState(true);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [activityTypeId, setActivityTypeId] = useState<string | null>(null);
    const [initError, setInitError] = useState<string>('');
    const [currentIndex, setCurrentIndex] = useState(0);
    const [score, setScore] = useState(0);
    const [finished, setFinished] = useState(false);
    const [selectedOption, setSelectedOption] = useState<string | null>(null);
    const [feedback, setFeedback] = useState<{ isCorrect: boolean, text: string } | null>(null);
    const [questionStartTime, setQuestionStartTime] = useState<Date>(new Date());
    const [answerMap, setAnswerMap] = useState<Record<string, { selectedOption: string; isCorrect: boolean }>>({});
    const [examEndsAtMs, setExamEndsAtMs] = useState<number | null>(null);
    const [timeLeftSec, setTimeLeftSec] = useState<number | null>(null);
    const [sessionFeedbackRating, setSessionFeedbackRating] = useState<number>(5);
    const [sessionFeedbackText, setSessionFeedbackText] = useState<string>('');
    const [sessionFeedbackSubmitting, setSessionFeedbackSubmitting] = useState(false);
    const [sessionFeedbackSubmitted, setSessionFeedbackSubmitted] = useState(false);
    const [sessionFeedbackError, setSessionFeedbackError] = useState<string>('');

    const formatTime = (totalSeconds: number) => {
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    };

    useEffect(() => {
        let cancelled = false;

        const initSession = async () => {
            try {
                setLoading(true);
                setInitError('');
                setItems([]);
                setSessionId(null);
                setActivityTypeId(null);
                setCurrentIndex(0);
                setScore(0);
                setFinished(false);
                setSelectedOption(null);
                setFeedback(null);
                setAnswerMap({});
                setSessionFeedbackSubmitted(false);
                setSessionFeedbackError('');
                setExamEndsAtMs(null);
                setTimeLeftSec(null);

                // 1. Get activity type
                const typesRes = await api.get('/activities/activity-types');
                const selectedType = typesRes.data.find((t: any) => t.code === activityCode);
                if (!selectedType) {
                    console.error('Activity type not found:', activityCode);
                    if (!cancelled) setInitError(`No se encontró el tipo de actividad ${activityCode}.`);
                    return;
                }
                if (!cancelled) setActivityTypeId(selectedType.id);

                // 2. Create activity session
                const sessionRes = await api.post('/activities/sessions', {
                    student_id: studentId,
                    activity_type_id: selectedType.id,
                    subject_id: subjectId,
                    term_id: termId,
                    topic_id: null,
                    item_count: itemCount,
                    content_upload_id: uploadId,
                    device_type: 'web'
                });
                if (!cancelled) setSessionId(sessionRes.data.id);

                // 3. Get session items (ordered)
                const sessionItemsRes = await api.get(`/activities/sessions/${sessionRes.data.id}/items`);
                if (!cancelled) {
                    setItems(sessionItemsRes.data);
                    setQuestionStartTime(new Date());
                    if (examMode && typeof timeLimitSeconds === 'number' && timeLimitSeconds > 0) {
                        const endsAt = Date.now() + timeLimitSeconds * 1000;
                        setExamEndsAtMs(endsAt);
                    }
                }

            } catch (err: any) {
                console.error('Error initializing session:', err);
                const detail = err?.response?.data?.detail;
                if (!cancelled) {
                    if (detail === 'Not enough permissions') {
                        setInitError('Necesitas iniciar sesión como estudiante.');
                    } else if (detail === 'No items found for this subject/term') {
                        setInitError('Este contenido aún no tiene preguntas para esta actividad. Pide al tutor que lo procese.');
                    } else if (typeof detail === 'string' && detail.length > 0) {
                        setInitError(detail);
                    } else {
                        setInitError(err?.message || 'No se pudo iniciar la sesión.');
                    }
                }
            } finally {
                if (!cancelled) setLoading(false);
            }
        };

        initSession();

        return () => {
            cancelled = true;
        };
    }, [uploadId, studentId, subjectId, termId, activityCode, examMode, itemCount, timeLimitSeconds]);

    const finishSession = useCallback(async () => {
        if (finished) return;
        try {
            await api.post(`/activities/sessions/${sessionId}/end`);
        } catch (err: any) {
            console.error('Error ending session:', err);
        }
        setFinished(true);
    }, [finished, sessionId]);

    useEffect(() => {
        if (!examMode) return;
        if (!examEndsAtMs) return;
        if (!sessionId) return;
        if (finished) return;

        const tick = () => {
            const remaining = Math.max(0, Math.ceil((examEndsAtMs - Date.now()) / 1000));
            setTimeLeftSec(remaining);
            if (remaining <= 0) {
                finishSession();
            }
        };

        tick();
        const timerId = setInterval(tick, 1000);
        return () => clearInterval(timerId);
    }, [examMode, examEndsAtMs, finished, sessionId, finishSession]);

    if (loading) return <p>Cargando preguntas...</p>;
    if (initError) {
        return (
            <div className="card" style={{ maxWidth: '600px', margin: '0 auto' }}>
                <h3 style={{ marginBottom: '0.75rem' }}>No se pudo iniciar la sesión</h3>
                <p style={{ color: 'var(--error)', marginTop: 0 }}>{initError}</p>
                <button onClick={onExit} className="btn">Volver</button>
            </div>
        );
    }
    if (!sessionId || !activityTypeId) return <p>Cargando sesión...</p>;
    if (items.length === 0) return <p>No hay preguntas disponibles para este contenido.</p>;

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

        setAnswerMap((prev) => ({ ...prev, [currentItem.id]: { selectedOption: option, isCorrect } }));
        if (isCorrect) setScore((s) => s + 1);

        if (!examMode) {
            if (isCorrect) {
                setFeedback({ isCorrect: true, text: "¡Correcto!" });
            } else {
                setFeedback({
                    isCorrect: false,
                    text: `Incorrecto. La respuesta correcta es: ${currentItem.correct_answer}. ${currentItem.explanation || ''}`
                });
            }
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
                <h3>{examMode ? 'Examen completado' : 'Actividad Completada'}</h3>
                <p style={{ fontSize: '2rem', margin: '2rem 0' }}>Score: {score} / {items.length}</p>
                <p style={{ color: 'var(--text-secondary)' }}>
                    Tus métricas se han actualizado automáticamente.
                </p>

                {examMode && (
                    <div style={{ marginTop: '1.5rem', textAlign: 'left' }}>
                        <h4 style={{ marginTop: 0 }}>Resumen</h4>
                        <div style={{ overflowX: 'auto' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                <thead>
                                    <tr style={{ textAlign: 'left', color: 'var(--text-secondary)' }}>
                                        <th style={{ padding: '0.5rem' }}>#</th>
                                        <th style={{ padding: '0.5rem' }}>Tu respuesta</th>
                                        <th style={{ padding: '0.5rem' }}>Correcta</th>
                                        <th style={{ padding: '0.5rem' }}>Resultado</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {items.map((it, idx) => {
                                        const entry = answerMap[it.id];
                                        const correct = entry?.isCorrect === true;
                                        return (
                                            <tr key={it.id} style={{ borderTop: '1px solid var(--border-color)' }}>
                                                <td style={{ padding: '0.5rem' }}>{idx + 1}</td>
                                                <td style={{ padding: '0.5rem' }}>{entry?.selectedOption ?? '-'}</td>
                                                <td style={{ padding: '0.5rem' }}>{it.correct_answer}</td>
                                                <td style={{ padding: '0.5rem', color: correct ? 'var(--success)' : 'var(--error)' }}>
                                                    {entry ? (correct ? 'Correcta' : 'Incorrecta') : 'Sin responder'}
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

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
                {examMode ? (
                    <span>{typeof timeLeftSec === 'number' ? `Tiempo: ${formatTime(timeLeftSec)}` : 'Tiempo: —'}</span>
                ) : (
                    <span>Score: {score}</span>
                )}
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
                                backgroundColor: examMode
                                    ? (selectedOption === opt ? 'var(--bg-secondary)' : 'var(--bg-primary)')
                                    : (selectedOption === opt
                                        ? (feedback?.isCorrect ? 'var(--success)' : 'var(--error)')
                                        : (selectedOption && opt === currentItem.correct_answer ? 'var(--success)' : 'var(--bg-primary)')),
                                color: examMode ? 'var(--text-primary)' : (selectedOption ? 'white' : 'var(--text-primary)'),
                                border: selectedOption === opt ? '1px solid var(--border-color)' : '1px solid var(--border-color)'
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

            {!examMode && feedback && (
                <div style={{ marginTop: '2rem', padding: '1rem', backgroundColor: 'var(--bg-primary)', borderRadius: 'var(--radius-md)' }}>
                    <p style={{ color: feedback.isCorrect ? 'var(--success)' : 'var(--error)', fontWeight: 'bold' }}>
                        {feedback.text}
                    </p>
                    <button onClick={nextQuestion} className="btn" style={{ marginTop: '1rem' }}>Siguiente</button>
                </div>
            )}

            {examMode && selectedOption && (
                <div style={{ marginTop: '2rem', padding: '1rem', backgroundColor: 'var(--bg-primary)', borderRadius: 'var(--radius-md)' }}>
                    <p style={{ color: 'var(--text-secondary)', fontWeight: 'bold' }}>
                        Respuesta guardada.
                    </p>
                    <button onClick={nextQuestion} className="btn" style={{ marginTop: '1rem' }}>
                        {currentIndex < items.length - 1 ? 'Siguiente' : 'Finalizar'}
                    </button>
                </div>
            )}
        </div>
    );
}
