"use client";

import { useEffect, useMemo, useState } from "react";
import {
    createMicroconcept,
    fetchMicroconcepts,
    fetchMicroconceptPrerequisites,
    addMicroconceptPrerequisite,
    removeMicroconceptPrerequisite,
    MicroConcept,
    MicroConceptPrerequisite,
    updateMicroconcept,
} from "../../services/microconcepts";

interface MicroconceptManagerProps {
    subjectId: string;
    termId: string;
}

function getErrorMessage(err: any): string {
    const detail = err?.response?.data?.detail;
    if (typeof detail === "string" && detail.length > 0) return detail;
    return err?.message || "Error cargando microconceptos.";
}

export default function MicroconceptManager({ subjectId, termId }: MicroconceptManagerProps) {
    const [items, setItems] = useState<MicroConcept[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const [createCode, setCreateCode] = useState("");
    const [createName, setCreateName] = useState("");
    const [createDescription, setCreateDescription] = useState("");
    const [creating, setCreating] = useState(false);

    const [editingId, setEditingId] = useState<string | null>(null);
    const editingItem = useMemo(
        () => items.find((i) => i.id === editingId) || null,
        [items, editingId]
    );
    const [editCode, setEditCode] = useState("");
    const [editName, setEditName] = useState("");
    const [editDescription, setEditDescription] = useState("");
    const [saving, setSaving] = useState(false);

    const [prereqOpenId, setPrereqOpenId] = useState<string | null>(null);
    const [prereqLoading, setPrereqLoading] = useState(false);
    const [prereqByMicroconcept, setPrereqByMicroconcept] = useState<
        Record<string, MicroConceptPrerequisite[]>
    >({});
    const [prereqSelection, setPrereqSelection] = useState<string[]>([]);
    const [prereqSaving, setPrereqSaving] = useState(false);

    const refresh = async () => {
        if (!subjectId) return;
        setLoading(true);
        setError("");
        try {
            const data = await fetchMicroconcepts({ subjectId, termId });
            setItems(data);
        } catch (err: any) {
            setError(getErrorMessage(err));
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        refresh();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [subjectId, termId]);

    useEffect(() => {
        if (!editingItem) return;
        setEditCode(editingItem.code || "");
        setEditName(editingItem.name || "");
        setEditDescription(editingItem.description || "");
    }, [editingItem]);

    const onCreate = async () => {
        if (!createName.trim()) {
            setError("El nombre es obligatorio.");
            return;
        }
        setCreating(true);
        setError("");
        try {
            const created = await createMicroconcept({
                subject_id: subjectId,
                term_id: termId || null,
                code: createCode.trim() || null,
                name: createName.trim(),
                description: createDescription.trim() || null,
                active: true,
            });
            setItems((prev) => [created, ...prev].sort((a, b) => a.name.localeCompare(b.name)));
            setCreateCode("");
            setCreateName("");
            setCreateDescription("");
        } catch (err: any) {
            setError(getErrorMessage(err));
        } finally {
            setCreating(false);
        }
    };

    const startEdit = (id: string) => {
        setEditingId(id);
        setError("");
    };

    const cancelEdit = () => {
        setEditingId(null);
        setError("");
    };

    const openPrereqEditor = async (microconceptId: string) => {
        if (prereqOpenId === microconceptId) {
            setPrereqOpenId(null);
            setPrereqSelection([]);
            return;
        }
        setPrereqOpenId(microconceptId);
        setPrereqLoading(true);
        setError("");
        try {
            const edges = await fetchMicroconceptPrerequisites(microconceptId);
            setPrereqByMicroconcept((prev) => ({ ...prev, [microconceptId]: edges }));
            setPrereqSelection(edges.map((e) => e.prerequisite_microconcept_id));
        } catch (err: any) {
            setError(getErrorMessage(err));
        } finally {
            setPrereqLoading(false);
        }
    };

    const savePrereqSelection = async () => {
        if (!prereqOpenId) return;
        setPrereqSaving(true);
        setError("");
        try {
            const current = prereqByMicroconcept[prereqOpenId] || [];
            const currentIds = new Set(current.map((e) => e.prerequisite_microconcept_id));
            const desiredIds = new Set(prereqSelection);

            const toAdd = prereqSelection.filter((id) => !currentIds.has(id));
            const toRemove = current
                .filter((edge) => !desiredIds.has(edge.prerequisite_microconcept_id))
                .map((edge) => edge.prerequisite_microconcept_id);

            if (toAdd.length > 0) {
                await Promise.all(toAdd.map((id) => addMicroconceptPrerequisite(prereqOpenId, id)));
            }
            if (toRemove.length > 0) {
                await Promise.all(toRemove.map((id) => removeMicroconceptPrerequisite(prereqOpenId, id)));
            }

            const edges = await fetchMicroconceptPrerequisites(prereqOpenId);
            setPrereqByMicroconcept((prev) => ({ ...prev, [prereqOpenId]: edges }));
        } catch (err: any) {
            setError(getErrorMessage(err));
        } finally {
            setPrereqSaving(false);
        }
    };

    const onSave = async () => {
        if (!editingId) return;
        if (!editName.trim()) {
            setError("El nombre es obligatorio.");
            return;
        }
        setSaving(true);
        setError("");
        try {
            const updated = await updateMicroconcept(editingId, {
                code: editCode.trim() || null,
                name: editName.trim(),
                description: editDescription.trim() || null,
            });
            setItems((prev) => prev.map((i) => (i.id === updated.id ? updated : i)));
            setEditingId(null);
        } catch (err: any) {
            setError(getErrorMessage(err));
        } finally {
            setSaving(false);
        }
    };

    const toggleActive = async (mc: MicroConcept) => {
        setError("");
        try {
            const updated = await updateMicroconcept(mc.id, { active: !mc.active });
            setItems((prev) => prev.map((i) => (i.id === updated.id ? updated : i)));
        } catch (err: any) {
            setError(getErrorMessage(err));
        }
    };

    return (
        <div className="card">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <h3 style={{ margin: 0 }}>Microconceptos</h3>
                <button className="btn btn-secondary" onClick={refresh} disabled={loading}>
                    {loading ? "Cargando..." : "Refrescar"}
                </button>
            </div>

            <div style={{ marginTop: "1rem", display: "grid", gap: "0.75rem" }}>
                <h4 style={{ margin: 0 }}>Nuevo microconcepto</h4>
                <div style={{ display: "grid", gridTemplateColumns: "160px 1fr", gap: "0.75rem" }}>
                    <input
                        className="input"
                        placeholder="Código (opcional)"
                        value={createCode}
                        onChange={(e) => setCreateCode(e.target.value)}
                        disabled={creating}
                    />
                    <input
                        className="input"
                        placeholder="Nombre *"
                        value={createName}
                        onChange={(e) => setCreateName(e.target.value)}
                        disabled={creating}
                    />
                </div>
                <textarea
                    className="input"
                    placeholder="Descripción (opcional)"
                    value={createDescription}
                    onChange={(e) => setCreateDescription(e.target.value)}
                    disabled={creating}
                />
                <button className="btn" onClick={onCreate} disabled={creating}>
                    {creating ? "Creando..." : "Crear microconcepto"}
                </button>
            </div>

            {error && (
                <p style={{ marginTop: "1rem", color: "var(--error)", fontWeight: 600 }}>{error}</p>
            )}

            <div style={{ marginTop: "1.5rem" }}>
                <h4 style={{ margin: 0 }}>Listado</h4>

                {items.length === 0 && !loading ? (
                    <p style={{ color: "var(--text-secondary)", marginTop: "0.75rem" }}>
                        No hay microconceptos todavía para este contexto.
                    </p>
                ) : (
                    <div style={{ marginTop: "0.75rem", display: "grid", gap: "0.75rem" }}>
                        {items.map((mc) => {
                            const isEditing = editingId === mc.id;
                            const isPrereqOpen = prereqOpenId === mc.id;
                            const prereqEdges = prereqByMicroconcept[mc.id] || [];
                            const prereqNames = prereqEdges
                                .map((e) => items.find((i) => i.id === e.prerequisite_microconcept_id)?.name)
                                .filter((n): n is string => typeof n === "string" && n.length > 0);

                            const prereqOptions = items
                                .filter((o) => o.id !== mc.id && o.term_id === mc.term_id)
                                .sort((a, b) => a.name.localeCompare(b.name));
                            return (
                                <div
                                    key={mc.id}
                                    className="card"
                                    style={{
                                        padding: "1rem",
                                        borderLeft: `4px solid ${
                                            mc.active ? "var(--success)" : "var(--border-color)"
                                        }`,
                                    }}
                                >
                                    <div
                                        style={{
                                            display: "flex",
                                            justifyContent: "space-between",
                                            gap: "1rem",
                                        }}
                                    >
                                        <div style={{ flex: 1, minWidth: 0 }}>
                                            {isEditing ? (
                                                <div style={{ display: "grid", gap: "0.5rem" }}>
                                                    <div
                                                        style={{
                                                            display: "grid",
                                                            gridTemplateColumns: "160px 1fr",
                                                            gap: "0.75rem",
                                                        }}
                                                    >
                                                        <input
                                                            className="input"
                                                            placeholder="Código"
                                                            value={editCode}
                                                            onChange={(e) => setEditCode(e.target.value)}
                                                            disabled={saving}
                                                        />
                                                        <input
                                                            className="input"
                                                            placeholder="Nombre *"
                                                            value={editName}
                                                            onChange={(e) => setEditName(e.target.value)}
                                                            disabled={saving}
                                                        />
                                                    </div>
                                                    <textarea
                                                        className="input"
                                                        placeholder="Descripción"
                                                        value={editDescription}
                                                        onChange={(e) => setEditDescription(e.target.value)}
                                                        disabled={saving}
                                                    />
                                                </div>
                                            ) : (
                                                <>
                                                    <div
                                                        style={{
                                                            display: "flex",
                                                            alignItems: "baseline",
                                                            gap: "0.75rem",
                                                        }}
                                                    >
                                                        <h4 style={{ margin: 0, wordBreak: "break-word" }}>
                                                            {mc.name}
                                                        </h4>
                                                        {mc.code && (
                                                            <span
                                                                style={{
                                                                    color: "var(--text-secondary)",
                                                                    fontSize: "0.9rem",
                                                                }}
                                                            >
                                                                {mc.code}
                                                            </span>
                                                        )}
                                                    </div>
                                                    {mc.description && (
                                                        <p
                                                            style={{
                                                                margin: "0.5rem 0 0 0",
                                                                color: "var(--text-secondary)",
                                                            }}
                                                        >
                                                            {mc.description}
                                                        </p>
                                                    )}
                                                </>
                                            )}
                                        </div>

                                        <div
                                            style={{
                                                display: "flex",
                                                flexDirection: "column",
                                                gap: "0.5rem",
                                                alignItems: "flex-end",
                                            }}
                                        >
                                            <span
                                                style={{
                                                    padding: "0.25rem 0.6rem",
                                                    borderRadius: "var(--radius-sm)",
                                                    backgroundColor: mc.active
                                                        ? "rgba(46, 204, 113, 0.15)"
                                                        : "rgba(255,255,255,0.06)",
                                                    color: mc.active
                                                        ? "var(--success)"
                                                        : "var(--text-secondary)",
                                                    fontWeight: 700,
                                                    fontSize: "0.85rem",
                                                }}
                                            >
                                                {mc.active ? "Activo" : "Inactivo"}
                                            </span>

                                            <button
                                                className="btn btn-secondary"
                                                onClick={() => toggleActive(mc)}
                                                disabled={saving || creating}
                                            >
                                                {mc.active ? "Desactivar" : "Activar"}
                                            </button>

                                            {isEditing ? (
                                                <div style={{ display: "flex", gap: "0.5rem" }}>
                                                    <button
                                                        className="btn"
                                                        onClick={onSave}
                                                        disabled={saving}
                                                    >
                                                        {saving ? "Guardando..." : "Guardar"}
                                                    </button>
                                                    <button
                                                        className="btn btn-secondary"
                                                        onClick={cancelEdit}
                                                        disabled={saving}
                                                    >
                                                        Cancelar
                                                    </button>
                                                </div>
                                            ) : (
                                                <div style={{ display: "flex", gap: "0.5rem" }}>
                                                    <button
                                                        className="btn btn-secondary"
                                                        onClick={() => startEdit(mc.id)}
                                                        disabled={saving || creating}
                                                    >
                                                        Editar
                                                    </button>
                                                    <button
                                                        className="btn btn-secondary"
                                                        onClick={() => openPrereqEditor(mc.id)}
                                                        disabled={saving || creating}
                                                    >
                                                        Prerequisitos
                                                    </button>
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    {!isEditing && (
                                        <div style={{ marginTop: "0.75rem", color: "var(--text-secondary)" }}>
                                            <strong>Prerequisitos:</strong>{" "}
                                            {prereqNames.length > 0 ? prereqNames.join(", ") : "—"}
                                        </div>
                                    )}

                                    {isPrereqOpen && !isEditing && (
                                        <div style={{ marginTop: "0.75rem" }}>
                                            {prereqLoading ? (
                                                <p style={{ color: "var(--text-secondary)", margin: 0 }}>
                                                    Cargando prerequisitos...
                                                </p>
                                            ) : (
                                                <>
                                                    <label style={{ display: "block", marginBottom: "0.5rem" }}>
                                                        Selecciona prerequisitos (múltiple)
                                                    </label>
                                                    <select
                                                        className="input"
                                                        multiple
                                                        value={prereqSelection}
                                                        onChange={(e) => {
                                                            const selected = Array.from(e.target.selectedOptions).map(
                                                                (o) => o.value
                                                            );
                                                            setPrereqSelection(selected);
                                                        }}
                                                        style={{ height: "140px" }}
                                                        disabled={prereqSaving}
                                                    >
                                                        {prereqOptions.map((o) => (
                                                            <option key={o.id} value={o.id}>
                                                                {o.name}
                                                            </option>
                                                        ))}
                                                    </select>
                                                    <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.75rem" }}>
                                                        <button
                                                            className="btn"
                                                            onClick={savePrereqSelection}
                                                            disabled={prereqSaving}
                                                        >
                                                            {prereqSaving ? "Guardando..." : "Guardar prerequisitos"}
                                                        </button>
                                                        <button
                                                            className="btn btn-secondary"
                                                            onClick={() => openPrereqEditor(mc.id)}
                                                            disabled={prereqSaving}
                                                        >
                                                            Cerrar
                                                        </button>
                                                    </div>
                                                </>
                                            )}
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
}
