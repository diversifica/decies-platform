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
    onExit: () => void;
}

export default function QuizRunner({ uploadId, onExit }: QuizRunnerProps) {
    const [items, setItems] = useState<Item[]>([]);
    const [loading, setLoading] = useState(true);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [score, setScore] = useState(0);
    const [finished, setFinished] = useState(false);
    const [selectedOption, setSelectedOption] = useState<string | null>(null);
    const [feedback, setFeedback] = useState<{ isCorrect: boolean, text: string } | null>(null);

    useEffect(() => {
        const fetchItems = async () => {
            try {
                const res = await api.get(`/content/uploads/${uploadId}/items`);
                setItems(res.data);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchItems();
    }, [uploadId]);

    if (loading) return <p>Cargando preguntas...</p>;
    if (items.length === 0) return <p>No hay preguntas disponibles para este contenido.</p>;

    const currentItem = items[currentIndex];

    const handleAnswer = (option: string) => {
        if (selectedOption) return; // Prevent double answer
        setSelectedOption(option);

        // Check answer
        // For True/False, typical options are "True", "False" or similar.
        // For MCQ, typical list.
        // Simple exact match check.
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
    };

    const nextQuestion = () => {
        setSelectedOption(null);
        setFeedback(null);
        if (currentIndex < items.length - 1) {
            setCurrentIndex(i => i + 1);
        } else {
            setFinished(true);
        }
    };

    if (finished) {
        return (
            <div className="card" style={{ textAlign: 'center' }}>
                <h3>Actividad Completada</h3>
                <p style={{ fontSize: '2rem', margin: '2rem 0' }}>Score: {score} / {items.length}</p>
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
                    /* Fallback for True/False if options missing? Usually LLM provides options for T/F too */
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
