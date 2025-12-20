"use client";

import { useEffect, useMemo, useState } from "react";
import api from "../../services/api";

interface Item {
    id: string;
    type: string;
    stem: string;
    options?: any;
    correct_answer: string;
    explanation?: string;
}

interface ClozeRunnerProps {
    uploadId: string;
    studentId: string;
    subjectId: string;
    termId: string;
    onExit: () => void;
}

function normalizeText(text: string): string {
    return text
        .normalize("NFKD")
        .replace(/[\u0300-\u036f]/g, "")
        .trim()
        .replace(/\s+/g, " ")
        .toLowerCase();
}

function parseAcceptableAnswers(correctAnswer: string): string[] {
    try {
        const parsed = JSON.parse(correctAnswer);
        if (Array.isArray(parsed)) {
            return parsed.filter((x) => typeof x === "string" || typeof x === "number").map(String);
        }
    } catch {
        // ignore
    }
    return [correctAnswer];
}

export default function ClozeRunner({ uploadId, studentId, subjectId, termId, onExit }: ClozeRunnerProps) {
    const [items, setItems] = useState<Item[]>([]);
    const [loading, setLoading] = useState(true);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [activityTypeId, setActivityTypeId] = useState<string | null>(null);
    const [initError, setInitError] = useState<string>("");

    const [currentIndex, setCurrentIndex] = useState(0);
    const [finished, setFinished] = useState(false);
    const [answer, setAnswer] = useState("");
    const [feedback, setFeedback] = useState<{ isCorrect: boolean; text: string } | null>(null);
    const [questionStartTime, setQuestionStartTime] = useState<Date>(new Date());

    const [sessionFeedbackRating, setSessionFeedbackRating] = useState<number>(5);
    const [sessionFeedbackText, setSessionFeedbackText] = useState<string>("");
    const [sessionFeedbackSubmitting, setSessionFeedbackSubmitting] = useState(false);
    const [sessionFeedbackSubmitted, setSessionFeedbackSubmitted] = useState(false);
    const [sessionFeedbackError, setSessionFeedbackError] = useState<string>("");

    const currentItem = useMemo(() => items[currentIndex], [items, currentIndex]);

    useEffect(() => {
        let cancelled = false;

        const initSession = async () => {
            try {
                setLoading(true);
                setInitError("");
                setItems([]);
                setSessionId(null);
                setActivityTypeId(null);
                setCurrentIndex(0);
                setFinished(false);
                setAnswer("");
                setFeedback(null);
                setSessionFeedbackSubmitted(false);
                setSessionFeedbackError("");

                const typesRes = await api.get("/activities/activity-types");
                const clozeType = typesRes.data.find((t: any) => t.code === "CLOZE");
                if (!clozeType) {
                    if (!cancelled) setInitError("No se encontró el tipo de actividad CLOZE.");
                    return;
                }
                if (!cancelled) setActivityTypeId(clozeType.id);

                const sessionRes = await api.post("/activities/sessions", {
                    student_id: studentId,
                    activity_type_id: clozeType.id,
                    subject_id: subjectId,
                    term_id: termId,
                    topic_id: null,
                    item_count: 10,
                    content_upload_id: uploadId,
                    device_type: "web",
                });
                const sid = sessionRes.data.id;
                if (!cancelled) setSessionId(sid);

                const itemsRes = await api.get(`/activities/sessions/${sid}/items`);
                if (!cancelled) {
                    setItems(itemsRes.data);
                    setQuestionStartTime(new Date());
                }
            } catch (err: any) {
                console.error("Error initializing CLOZE session:", err);
                const detail = err?.response?.data?.detail;
                if (!cancelled) {
                    if (detail === "Not enough permissions") {
                        setInitError("Necesitas iniciar sesión como estudiante.");
                    } else if (detail === "No items found for this subject/term") {
                        setInitError("Este contenido aún no tiene ítems CLOZE. Por ahora usa Quiz.");
                    } else if (typeof detail === "string" && detail.length > 0) {
                        setInitError(detail);
                    } else {
                        setInitError(err?.message || "No se pudo iniciar la sesión.");
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
    }, [uploadId, studentId, subjectId, termId]);

    const submit = async () => {
        if (!sessionId || !activityTypeId || !currentItem) return;
        const endTime = new Date();
        const durationMs = endTime.getTime() - questionStartTime.getTime();

        const acceptable = parseAcceptableAnswers(currentItem.correct_answer).map(normalizeText);
        const submitted = normalizeText(answer);
        const isCorrectLocal = acceptable.includes(submitted);

        setFeedback({
            isCorrect: isCorrectLocal,
            text: isCorrectLocal
                ? "Correcto."
                : `Incorrecto. Respuesta: ${parseAcceptableAnswers(currentItem.correct_answer).join(" / ")}. ${
                      currentItem.explanation || ""
                  }`,
        });

        try {
            const resp = await api.post(`/activities/sessions/${sessionId}/responses`, {
                student_id: studentId,
                item_id: currentItem.id,
                subject_id: subjectId,
                term_id: termId,
                topic_id: null,
                microconcept_id: null,
                activity_type_id: activityTypeId,
                is_correct: isCorrectLocal,
                duration_ms: durationMs,
                attempt_number: 1,
                response_normalized: answer,
                hint_used: null,
                difficulty_at_time: null,
                timestamp_start: questionStartTime.toISOString(),
                timestamp_end: endTime.toISOString(),
            });

            if (typeof resp?.data?.is_correct === "boolean") {
                const backendCorrect = resp.data.is_correct;
                if (backendCorrect !== isCorrectLocal) {
                    setFeedback({
                        isCorrect: backendCorrect,
                        text: backendCorrect
                            ? "Correcto."
                            : `Incorrecto. Respuesta: ${parseAcceptableAnswers(
                                  currentItem.correct_answer
                              ).join(" / ")}. ${currentItem.explanation || ""}`,
                    });
                }
            }
        } catch (err: any) {
            console.error("Error recording event:", err);
        }
    };

    const next = async () => {
        setAnswer("");
        setFeedback(null);
        setQuestionStartTime(new Date());
        if (currentIndex < items.length - 1) {
            setCurrentIndex((i) => i + 1);
            return;
        }
        try {
            await api.post(`/activities/sessions/${sessionId}/end`);
        } catch (err: any) {
            console.error("Error ending session:", err);
        }
        setFinished(true);
    };

    const submitSessionFeedback = async () => {
        if (!sessionId || sessionFeedbackSubmitted) return;
        setSessionFeedbackSubmitting(true);
        setSessionFeedbackError("");
        try {
            await api.post(`/activities/sessions/${sessionId}/feedback`, {
                rating: sessionFeedbackRating,
                text: sessionFeedbackText || null,
            });
            setSessionFeedbackSubmitted(true);
        } catch (err: any) {
            setSessionFeedbackError(err?.response?.data?.detail || err?.message || "Error enviando feedback");
        } finally {
            setSessionFeedbackSubmitting(false);
        }
    };

    if (loading) return <p>Cargando cloze...</p>;
    if (initError) {
        return (
            <div className="card" style={{ maxWidth: "600px", margin: "0 auto" }}>
                <h3 style={{ marginBottom: "0.75rem" }}>No se pudo iniciar la sesión</h3>
                <p style={{ color: "var(--error)", marginTop: 0 }}>{initError}</p>
                <button onClick={onExit} className="btn">
                    Volver
                </button>
            </div>
        );
    }
    if (!currentItem) return <p>No hay ítems CLOZE disponibles para este contenido.</p>;

    if (finished) {
        return (
            <div className="card" style={{ textAlign: "center" }}>
                <h3>Actividad Completada</h3>
                <p style={{ color: "var(--text-secondary)" }}>
                    Tus métricas se han actualizado automáticamente.
                </p>

                <div style={{ marginTop: "1.5rem", textAlign: "left" }}>
                    <h4 style={{ marginTop: 0 }}>Feedback (opcional)</h4>
                    <label style={{ display: "block", marginBottom: "0.75rem" }}>
                        Valoración
                        <select
                            className="input"
                            value={sessionFeedbackRating}
                            onChange={(e) => setSessionFeedbackRating(Number(e.target.value))}
                            disabled={sessionFeedbackSubmitting || sessionFeedbackSubmitted}
                        >
                            {[1, 2, 3, 4, 5].map((v) => (
                                <option key={v} value={v}>
                                    {v}
                                </option>
                            ))}
                        </select>
                    </label>
                    <label style={{ display: "block" }}>
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
                        <p style={{ color: "var(--error)", marginTop: "0.75rem" }}>{sessionFeedbackError}</p>
                    )}
                    {sessionFeedbackSubmitted && (
                        <p style={{ color: "var(--success)", marginTop: "0.75rem" }}>Feedback enviado.</p>
                    )}
                    <button
                        onClick={submitSessionFeedback}
                        className="btn btn-secondary"
                        disabled={sessionFeedbackSubmitting || sessionFeedbackSubmitted}
                        style={{ marginTop: "0.75rem" }}
                    >
                        {sessionFeedbackSubmitting ? "Enviando..." : "Enviar feedback"}
                    </button>
                </div>

                <button onClick={onExit} className="btn" style={{ marginTop: "1rem" }}>
                    Volver al inicio
                </button>
            </div>
        );
    }

    return (
        <div className="card" style={{ maxWidth: "700px", margin: "0 auto" }}>
            <div
                style={{
                    display: "flex",
                    justifyContent: "space-between",
                    marginBottom: "1rem",
                    color: "var(--text-secondary)",
                }}
            >
                <span>Ítem {currentIndex + 1} de {items.length}</span>
                <span>CLOZE</span>
            </div>

            <h3 style={{ marginBottom: "1rem" }}>{currentItem.stem}</h3>

            <input
                className="input"
                placeholder={currentItem.options?.placeholder || "Respuesta"}
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                disabled={!!feedback}
            />

            <div style={{ display: "flex", gap: "0.75rem", marginTop: "1.25rem" }}>
                <button className="btn" onClick={submit} disabled={!!feedback || answer.trim().length === 0}>
                    Enviar
                </button>
                {feedback && (
                    <button className="btn btn-secondary" onClick={next}>
                        Siguiente
                    </button>
                )}
            </div>

            {feedback && (
                <div
                    style={{
                        marginTop: "1rem",
                        padding: "1rem",
                        backgroundColor: "var(--bg-primary)",
                        borderRadius: "var(--radius-md)",
                    }}
                >
                    <p style={{ color: feedback.isCorrect ? "var(--success)" : "var(--error)", fontWeight: "bold" }}>
                        {feedback.text}
                    </p>
                </div>
            )}
        </div>
    );
}

