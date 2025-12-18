"use client";

import { Fragment, useEffect, useMemo, useState } from "react";
import api from "../../services/api";

type MatchPair = { left: string; right: string };

interface Item {
    id: string;
    type: string;
    stem: string;
    options?: any;
    correct_answer: string;
    explanation?: string;
}

interface MatchRunnerProps {
    uploadId: string;
    studentId: string;
    subjectId: string;
    termId: string;
    onExit: () => void;
}

function getPairs(item: Item): MatchPair[] {
    const pairs = item.options?.pairs;
    if (!Array.isArray(pairs)) return [];
    return pairs
        .filter((p) => p && typeof p.left === "string" && typeof p.right === "string")
        .map((p) => ({ left: p.left, right: p.right }));
}

function shuffle<T>(arr: T[]): T[] {
    const copy = [...arr];
    for (let i = copy.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [copy[i], copy[j]] = [copy[j], copy[i]];
    }
    return copy;
}

export default function MatchRunner({ uploadId, studentId, subjectId, termId, onExit }: MatchRunnerProps) {
    const [items, setItems] = useState<Item[]>([]);
    const [loading, setLoading] = useState(true);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [activityTypeId, setActivityTypeId] = useState<string | null>(null);
    const [initError, setInitError] = useState<string>('');
    const [currentIndex, setCurrentIndex] = useState(0);
    const [finished, setFinished] = useState(false);
    const [assignments, setAssignments] = useState<Record<string, string>>({});
    const [feedback, setFeedback] = useState<{ isCorrect: boolean; text: string } | null>(null);
    const [questionStartTime, setQuestionStartTime] = useState<Date>(new Date());

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
                setFinished(false);
                setAssignments({});
                setFeedback(null);

                const typesRes = await api.get("/activities/activity-types");
                const matchType = typesRes.data.find((t: any) => t.code === "MATCH");
                if (!matchType) {
                    console.error("MATCH activity type not found");
                    if (!cancelled) setInitError('No se encontró el tipo de actividad MATCH.');
                    return;
                }
                if (!cancelled) setActivityTypeId(matchType.id);

                const sessionRes = await api.post("/activities/sessions", {
                    student_id: studentId,
                    activity_type_id: matchType.id,
                    subject_id: subjectId,
                    term_id: termId,
                    topic_id: null,
                    item_count: 5,
                    content_upload_id: uploadId,
                    device_type: "web",
                });
                const sid = sessionRes.data.id;
                if (!cancelled) setSessionId(sid);

                const itemsRes = await api.get(`/activities/sessions/${sid}/items`);
                if (!cancelled) setItems(itemsRes.data);

                if (!cancelled) setQuestionStartTime(new Date());
            } catch (err: any) {
                console.error("Error initializing session:", err);
                const detail = err?.response?.data?.detail;
                if (!cancelled) {
                    if (detail === 'Not enough permissions') {
                        setInitError('Necesitas iniciar sesión como estudiante.');
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
    }, [uploadId, studentId, subjectId, termId]);

    const currentItem = items[currentIndex];
    const pairs = useMemo(() => (currentItem ? getPairs(currentItem) : []), [currentItem]);
    const rightOptions = useMemo(() => shuffle(pairs.map((p) => p.right)), [pairs]);

    useEffect(() => {
        setAssignments({});
        setFeedback(null);
        setQuestionStartTime(new Date());
    }, [currentIndex]);

    if (loading) return <p>Cargando actividad...</p>;
    if (initError) {
        return (
            <div className="card" style={{ maxWidth: "700px", margin: "0 auto" }}>
                <h3 style={{ marginBottom: "0.75rem" }}>No se pudo iniciar la sesión</h3>
                <p style={{ color: "var(--error)", marginTop: 0 }}>{initError}</p>
                <button onClick={onExit} className="btn">
                    Volver
                </button>
            </div>
        );
    }
    if (!sessionId || !activityTypeId) return <p>Cargando sesión...</p>;
    if (items.length === 0) return <p>No hay ítems MATCH disponibles para este contenido.</p>;

    const submit = async () => {
        if (feedback) return;
        const endTime = new Date();
        const durationMs = endTime.getTime() - questionStartTime.getTime();

        const isComplete = pairs.every((p) => assignments[p.left]);
        const isCorrect = isComplete && pairs.every((p) => assignments[p.left] === p.right);

        setFeedback({
            isCorrect,
            text: isCorrect ? "Correcto." : "Revisa tus emparejamientos e inténtalo de nuevo en la siguiente.",
        });

        try {
            await api.post(`/activities/sessions/${sessionId}/responses`, {
                student_id: studentId,
                item_id: currentItem.id,
                subject_id: subjectId,
                term_id: termId,
                topic_id: null,
                microconcept_id: null,
                activity_type_id: activityTypeId,
                is_correct: isCorrect,
                duration_ms: durationMs,
                attempt_number: 1,
                response_normalized: JSON.stringify(assignments),
                hint_used: null,
                difficulty_at_time: null,
                timestamp_start: questionStartTime.toISOString(),
                timestamp_end: endTime.toISOString(),
            });
        } catch (err: any) {
            console.error("Error recording event:", err);
        }
    };

    const next = async () => {
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

    if (finished) {
        return (
            <div className="card" style={{ textAlign: "center" }}>
                <h3>Actividad Completada</h3>
                <p style={{ color: "var(--text-secondary)" }}>Tus métricas se han actualizado automáticamente.</p>
                <button onClick={onExit} className="btn">
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
                <span>MATCH</span>
            </div>

            <h3 style={{ marginBottom: "1.5rem" }}>{currentItem.stem}</h3>

            {pairs.length === 0 ? (
                <p>Error: el ítem no tiene pares configurados.</p>
            ) : (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                    <div style={{ fontWeight: 600, color: "var(--text-secondary)" }}>Izquierda</div>
                    <div style={{ fontWeight: 600, color: "var(--text-secondary)" }}>Derecha</div>

                    {pairs.map((pair) => (
                        <Fragment key={pair.left}>
                            <div className="input" style={{ display: "flex", alignItems: "center" }}>
                                {pair.left}
                            </div>
                            <select
                                className="input"
                                value={assignments[pair.left] || ""}
                                onChange={(e) =>
                                    setAssignments((prev) => ({ ...prev, [pair.left]: e.target.value }))
                                }
                                disabled={!!feedback}
                            >
                                <option value="" disabled>
                                    Selecciona…
                                </option>
                                {rightOptions
                                    .filter((opt) => {
                                        const current = assignments[pair.left];
                                        if (opt === current) return true;
                                        return !Object.values(assignments).includes(opt);
                                    })
                                    .map((opt) => (
                                        <option key={opt} value={opt}>
                                            {opt}
                                        </option>
                                    ))}
                            </select>
                        </Fragment>
                    ))}
                </div>
            )}

            <div style={{ display: "flex", gap: "0.75rem", marginTop: "1.5rem" }}>
                <button className="btn" onClick={submit} disabled={!!feedback || pairs.length === 0}>
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
