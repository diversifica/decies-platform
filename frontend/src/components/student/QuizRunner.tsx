"use client";

import { useEffect, useState } from 'react';
import api from '../../services/api';

interface Item {
    id: string;
    type: string;
    stem: string;
    options?: string[];
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

    useEffect(() => {
        const initSession = async () => {
            try {
                // 1. Get items
                const itemsRes = await api.get(`/content/uploads/${uploadId}/items`);
                setItems(itemsRes.data);

                // 2. Get QUIZ activity type
                const typesRes = await api.get('/activities/activity-types');
                const quizType = typesRes.data.find((t: any) => t.code === 'QUIZ');
                if (!quizType) {
                    console.error('QUIZ activity type not found');
                    setLoading(false);
                    return;
                }
                setActivityTypeId(quizType.id);

                // 3. Create activity session
                const sessionRes = await api.post('/activities/sessions', {
                    student_id: studentId,
                    activity_type_id: quizType.id,
                    subject_id: subjectId,
                    term_id: termId,
                    topic_id: null,
                    item_count: 10,
                    device_type: 'web'
                });
                setSessionId(sessionRes.data.id);
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

    if (finished) {
        return (
            <div className="card" style={{ textAlign: 'center' }}>
                <h3>Actividad Completada</h3>
                <p style={{ fontSize: '2rem', margin: '2rem 0' }}>Score: {score} / {items.length}</p>
                <p style={{ color: 'var(--text-secondary)' }}>
                    Tus métricas se han actualizado automáticamente.
                </p>
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
                {currentItem.options ? (
                    currentItem.options.map((opt, idx) => (
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
