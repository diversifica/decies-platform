"use client";

import { useEffect, useMemo, useState } from "react";
import { fetchMicroconcepts, MicroConcept } from "../../services/microconcepts";
import { fetchTopics, TopicSummary } from "../../services/catalog";
import {
    addGradeTag,
    AssessmentScopeTagCreatePayload,
    createGrade,
    deleteGrade,
    deleteGradeTag,
    fetchGrades,
    RealGrade,
    updateGrade,
} from "../../services/grades";

interface RealGradesPanelProps {
    studentId: string;
    subjectId: string;
    termId: string;
}

type Mode = "create" | "edit";

export default function RealGradesPanel({ studentId, subjectId, termId }: RealGradesPanelProps) {
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const [grades, setGrades] = useState<RealGrade[]>([]);
    const [selectedGradeId, setSelectedGradeId] = useState<string | null>(null);

    const [topics, setTopics] = useState<TopicSummary[]>([]);
    const [microconcepts, setMicroconcepts] = useState<MicroConcept[]>([]);

    const selectedGrade = useMemo(
        () => grades.find((g) => g.id === selectedGradeId) ?? null,
        [grades, selectedGradeId]
    );

    const [mode, setMode] = useState<Mode>("create");
    const [assessmentDate, setAssessmentDate] = useState<string>("");
    const [gradeValue, setGradeValue] = useState<string>("");
    const [gradingScale, setGradingScale] = useState<string>("");
    const [notes, setNotes] = useState<string>("");

    const [draftTags, setDraftTags] = useState<AssessmentScopeTagCreatePayload[]>([]);
    const [tagTopicId, setTagTopicId] = useState<string>("");
    const [tagMicroconceptId, setTagMicroconceptId] = useState<string>("");
    const [tagWeight, setTagWeight] = useState<string>("");

    const topicById = useMemo(() => new Map(topics.map((t) => [t.id, t])), [topics]);
    const microconceptById = useMemo(
        () => new Map(microconcepts.map((m) => [m.id, m])),
        [microconcepts]
    );

    const resetForm = () => {
        setMode("create");
        setSelectedGradeId(null);
        setAssessmentDate("");
        setGradeValue("");
        setGradingScale("");
        setNotes("");
        setDraftTags([]);
        setTagTopicId("");
        setTagMicroconceptId("");
        setTagWeight("");
        setError(null);
    };

    const load = async () => {
        setLoading(true);
        setError(null);
        try {
            const [gradesData, topicsData, microconceptsData] = await Promise.all([
                fetchGrades({ studentId, subjectId, termId }),
                fetchTopics({ mine: true, subjectId, termId }),
                fetchMicroconcepts({ subjectId, termId }),
            ]);
            setGrades(gradesData);
            setTopics(topicsData);
            setMicroconcepts(microconceptsData);
        } catch (err: any) {
            setError(err?.response?.data?.detail || err.message || "Error cargando calificaciones");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        resetForm();
        if (!studentId || !subjectId || !termId) return;
        load();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [studentId, subjectId, termId]);

    useEffect(() => {
        if (!selectedGrade) return;
        setMode("edit");
        setAssessmentDate(selectedGrade.assessment_date ?? "");
        setGradeValue(String(selectedGrade.grade_value ?? ""));
        setGradingScale(selectedGrade.grading_scale ?? "");
        setNotes(selectedGrade.notes ?? "");
        setDraftTags([]);
        setTagTopicId("");
        setTagMicroconceptId("");
        setTagWeight("");
        setError(null);
    }, [selectedGrade]);

    const addDraftTag = () => {
        setError(null);
        if (!tagTopicId && !tagMicroconceptId) {
            setError("Selecciona un topic o un microconcepto para el tag.");
            return;
        }
        const weight = tagWeight ? Number(tagWeight) : null;
        if (tagWeight && Number.isNaN(weight)) {
            setError("El peso debe ser un número válido.");
            return;
        }
        setDraftTags((prev) => [
            ...prev,
            {
                topic_id: tagTopicId || null,
                microconcept_id: tagMicroconceptId || null,
                weight,
            },
        ]);
        setTagTopicId("");
        setTagMicroconceptId("");
        setTagWeight("");
    };

    const removeDraftTag = (index: number) => {
        setDraftTags((prev) => prev.filter((_, i) => i !== index));
    };

    const onSubmit = async () => {
        setSaving(true);
        setError(null);
        try {
            if (mode === "create") {
                const created = await createGrade({
                    student_id: studentId,
                    subject_id: subjectId,
                    term_id: termId,
                    assessment_date: assessmentDate,
                    grade_value: Number(gradeValue),
                    grading_scale: gradingScale || null,
                    notes: notes || null,
                    scope_tags: draftTags,
                });
                setGrades((prev) => [created, ...prev]);
                resetForm();
            } else if (selectedGrade) {
                const updated = await updateGrade(selectedGrade.id, {
                    assessment_date: assessmentDate,
                    grade_value: Number(gradeValue),
                    grading_scale: gradingScale || null,
                    notes: notes || null,
                });
                setGrades((prev) => prev.map((g) => (g.id === updated.id ? updated : g)));
            }
        } catch (err: any) {
            setError(err?.response?.data?.detail || err.message || "Error guardando calificación");
        } finally {
            setSaving(false);
        }
    };

    const onDeleteGrade = async (gradeId: string) => {
        if (!confirm("¿Borrar esta calificación?")) return;
        setSaving(true);
        setError(null);
        try {
            await deleteGrade(gradeId);
            setGrades((prev) => prev.filter((g) => g.id !== gradeId));
            if (selectedGradeId === gradeId) resetForm();
        } catch (err: any) {
            setError(err?.response?.data?.detail || err.message || "Error borrando calificación");
        } finally {
            setSaving(false);
        }
    };

    const onAddTagToGrade = async () => {
        if (!selectedGrade) return;
        setSaving(true);
        setError(null);
        try {
            if (!tagTopicId && !tagMicroconceptId) {
                setError("Selecciona un topic o un microconcepto para el tag.");
                return;
            }
            const weight = tagWeight ? Number(tagWeight) : null;
            if (tagWeight && Number.isNaN(weight)) {
                setError("El peso debe ser un número válido.");
                return;
            }
            const createdTag = await addGradeTag(selectedGrade.id, {
                topic_id: tagTopicId || null,
                microconcept_id: tagMicroconceptId || null,
                weight,
            });
            setGrades((prev) =>
                prev.map((g) =>
                    g.id === selectedGrade.id ? { ...g, scope_tags: [...g.scope_tags, createdTag] } : g
                )
            );
            setTagTopicId("");
            setTagMicroconceptId("");
            setTagWeight("");
        } catch (err: any) {
            setError(err?.response?.data?.detail || err.message || "Error añadiendo tag");
        } finally {
            setSaving(false);
        }
    };

    const onDeleteTag = async (tagId: string) => {
        if (!selectedGrade) return;
        setSaving(true);
        setError(null);
        try {
            await deleteGradeTag(selectedGrade.id, tagId);
            setGrades((prev) =>
                prev.map((g) =>
                    g.id === selectedGrade.id
                        ? { ...g, scope_tags: g.scope_tags.filter((t) => t.id !== tagId) }
                        : g
                )
            );
        } catch (err: any) {
            setError(err?.response?.data?.detail || err.message || "Error borrando tag");
        } finally {
            setSaving(false);
        }
    };

    const canSubmit = assessmentDate && gradeValue.trim() !== "" && !Number.isNaN(Number(gradeValue));

    if (loading) return <p>Cargando calificaciones...</p>;

    return (
        <div style={{ display: "grid", gap: "1.5rem" }}>
            <div className="card" style={{ padding: "1.25rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap" }}>
                    <div>
                        <h3 style={{ margin: 0 }}>Calificaciones reales</h3>
                        <p style={{ margin: "0.25rem 0 0", color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                            Registra examenes/entregas y su alcance por topic o microconcepto.
                        </p>
                    </div>
                    <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
                        <button className="btn btn-secondary" onClick={load} disabled={saving}>
                            Refrescar
                        </button>
                        <button className="btn btn-secondary" onClick={resetForm} disabled={saving}>
                            Nueva
                        </button>
                    </div>
                </div>

                {error && <p style={{ marginTop: "1rem", color: "var(--error)" }}>{error}</p>}

                {grades.length === 0 ? (
                    <p style={{ marginTop: "1rem", color: "var(--text-secondary)" }}>
                        Todavia no hay calificaciones registradas para este contexto.
                    </p>
                ) : (
                    <div style={{ marginTop: "1rem", overflowX: "auto" }}>
                        <table style={{ width: "100%", borderCollapse: "collapse" }}>
                            <thead>
                                <tr style={{ textAlign: "left", color: "var(--text-secondary)" }}>
                                    <th style={{ padding: "0.5rem" }}>Fecha</th>
                                    <th style={{ padding: "0.5rem" }}>Nota</th>
                                    <th style={{ padding: "0.5rem" }}>Escala</th>
                                    <th style={{ padding: "0.5rem" }}>Tags</th>
                                    <th style={{ padding: "0.5rem" }}>Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                {grades.map((grade) => {
                                    const isSelected = grade.id === selectedGradeId;
                                    return (
                                        <tr
                                            key={grade.id}
                                            style={{
                                                borderTop: "1px solid var(--border-color)",
                                                background: isSelected ? "rgba(124, 58, 237, 0.08)" : "transparent",
                                                cursor: "pointer",
                                            }}
                                            onClick={() => setSelectedGradeId(grade.id)}
                                        >
                                            <td style={{ padding: "0.5rem" }}>{grade.assessment_date}</td>
                                            <td style={{ padding: "0.5rem" }}>{grade.grade_value}</td>
                                            <td style={{ padding: "0.5rem" }}>{grade.grading_scale || "-"}</td>
                                            <td style={{ padding: "0.5rem" }}>{grade.scope_tags?.length || 0}</td>
                                            <td style={{ padding: "0.5rem", display: "flex", gap: "0.5rem" }}>
                                                <button
                                                    className="btn btn-secondary"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        setSelectedGradeId(grade.id);
                                                    }}
                                                >
                                                    Editar
                                                </button>
                                                <button
                                                    className="btn btn-secondary"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        onDeleteGrade(grade.id);
                                                    }}
                                                    disabled={saving}
                                                >
                                                    Borrar
                                                </button>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            <div className="card" style={{ padding: "1.25rem" }}>
                <h3 style={{ marginTop: 0 }}>{mode === "create" ? "Nueva calificacion" : "Editar calificacion"}</h3>

                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem" }}>
                    <label>
                        Fecha
                        <input
                            className="input"
                            type="date"
                            value={assessmentDate}
                            onChange={(e) => setAssessmentDate(e.target.value)}
                        />
                    </label>
                    <label>
                        Nota
                        <input
                            className="input"
                            type="number"
                            step="0.01"
                            value={gradeValue}
                            onChange={(e) => setGradeValue(e.target.value)}
                            placeholder="7.5"
                        />
                    </label>
                    <label>
                        Escala (opcional)
                        <input
                            className="input"
                            value={gradingScale}
                            onChange={(e) => setGradingScale(e.target.value)}
                            placeholder="0-10"
                        />
                    </label>
                </div>

                <label style={{ display: "block", marginTop: "1rem" }}>
                    Notas (opcional)
                    <textarea
                        className="input"
                        style={{ minHeight: "90px" }}
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                        placeholder="Comentario breve..."
                    />
                </label>

                <div style={{ marginTop: "1rem" }}>
                    <h4 style={{ margin: "0 0 0.5rem" }}>Tags de alcance</h4>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem" }}>
                        <label>
                            Topic (opcional)
                            <select className="input" value={tagTopicId} onChange={(e) => setTagTopicId(e.target.value)}>
                                <option value="">(ninguno)</option>
                                {topics.map((t) => (
                                    <option key={t.id} value={t.id}>
                                        {t.name}
                                    </option>
                                ))}
                            </select>
                        </label>
                        <label>
                            Microconcepto (opcional)
                            <select
                                className="input"
                                value={tagMicroconceptId}
                                onChange={(e) => setTagMicroconceptId(e.target.value)}
                            >
                                <option value="">(ninguno)</option>
                                {microconcepts
                                    .filter((m) => m.active)
                                    .map((m) => (
                                        <option key={m.id} value={m.id}>
                                            {m.name}
                                        </option>
                                    ))}
                            </select>
                        </label>
                        <label>
                            Peso (opcional)
                            <input
                                className="input"
                                type="number"
                                step="0.0001"
                                value={tagWeight}
                                onChange={(e) => setTagWeight(e.target.value)}
                                placeholder="1.0"
                            />
                        </label>
                    </div>

                    {mode === "create" ? (
                        <>
                            <div style={{ marginTop: "0.75rem", display: "flex", gap: "0.75rem" }}>
                                <button className="btn btn-secondary" onClick={addDraftTag} disabled={saving}>
                                    Añadir tag a la nueva calificacion
                                </button>
                            </div>
                            {draftTags.length > 0 && (
                                <div style={{ marginTop: "0.75rem", display: "grid", gap: "0.5rem" }}>
                                    {draftTags.map((t, idx) => (
                                        <div
                                            key={`${t.topic_id}-${t.microconcept_id}-${idx}`}
                                            style={{
                                                display: "flex",
                                                justifyContent: "space-between",
                                                alignItems: "center",
                                                padding: "0.5rem 0.75rem",
                                                background: "var(--bg-secondary)",
                                                borderRadius: "var(--radius-md)",
                                            }}
                                        >
                                            <div style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                                                {(t.topic_id && `Topic: ${topicById.get(t.topic_id)?.name ?? t.topic_id}`) ||
                                                    "(sin topic)"}
                                                {" · "}
                                                {(t.microconcept_id &&
                                                    `Microconcepto: ${microconceptById.get(t.microconcept_id)?.name ?? t.microconcept_id}`) ||
                                                    "(sin microconcepto)"}
                                                {t.weight != null ? ` · peso ${t.weight}` : ""}
                                            </div>
                                            <button className="btn btn-secondary" onClick={() => removeDraftTag(idx)}>
                                                Quitar
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </>
                    ) : (
                        <>
                            <div style={{ marginTop: "0.75rem", display: "flex", gap: "0.75rem" }}>
                                <button className="btn btn-secondary" onClick={onAddTagToGrade} disabled={saving || !selectedGrade}>
                                    Añadir tag a esta calificacion
                                </button>
                            </div>

                            {selectedGrade?.scope_tags?.length ? (
                                <div style={{ marginTop: "0.75rem", display: "grid", gap: "0.5rem" }}>
                                    {selectedGrade.scope_tags.map((t) => (
                                        <div
                                            key={t.id}
                                            style={{
                                                display: "flex",
                                                justifyContent: "space-between",
                                                alignItems: "center",
                                                padding: "0.5rem 0.75rem",
                                                background: "var(--bg-secondary)",
                                                borderRadius: "var(--radius-md)",
                                            }}
                                        >
                                            <div style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                                                {(t.topic_id && `Topic: ${topicById.get(t.topic_id)?.name ?? t.topic_id}`) ||
                                                    "(sin topic)"}
                                                {" · "}
                                                {(t.microconcept_id &&
                                                    `Microconcepto: ${microconceptById.get(t.microconcept_id)?.name ?? t.microconcept_id}`) ||
                                                    "(sin microconcepto)"}
                                                {t.weight != null ? ` · peso ${t.weight}` : ""}
                                            </div>
                                            <button className="btn btn-secondary" onClick={() => onDeleteTag(t.id)} disabled={saving}>
                                                Borrar
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p style={{ marginTop: "0.75rem", color: "var(--text-secondary)" }}>
                                    Esta calificacion aun no tiene tags.
                                </p>
                            )}
                        </>
                    )}
                </div>

                <div style={{ marginTop: "1.25rem", display: "flex", gap: "0.75rem", alignItems: "center" }}>
                    <button className="btn" onClick={onSubmit} disabled={saving || !canSubmit}>
                        {saving ? "Guardando..." : mode === "create" ? "Crear" : "Guardar"}
                    </button>
                    {mode === "edit" && (
                        <button className="btn btn-secondary" onClick={resetForm} disabled={saving}>
                            Cancelar
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}
