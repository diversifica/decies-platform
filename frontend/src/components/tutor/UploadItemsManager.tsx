"use client";

import { useEffect, useMemo, useState } from "react";
import api from "../../services/api";

interface UploadItemsManagerProps {
    uploadId: string;
    onClose: () => void;
}

interface ItemRow {
    id: string;
    type: string;
    stem: string;
    is_active?: boolean;
    microconcept_id?: string | null;
}

function summarizeStem(stem: string): string {
    const clean = (stem || "").replace(/\s+/g, " ").trim();
    if (clean.length <= 90) return clean;
    return `${clean.slice(0, 87)}...`;
}

export default function UploadItemsManager({ uploadId, onClose }: UploadItemsManagerProps) {
    const [items, setItems] = useState<ItemRow[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [savingId, setSavingId] = useState<string | null>(null);

    const activeCount = useMemo(() => items.filter((i) => i.is_active !== false).length, [items]);

    const fetchItems = async () => {
        setLoading(true);
        setError("");
        try {
            const res = await api.get(`/content/uploads/${uploadId}/items`);
            setItems(res.data);
        } catch (err: any) {
            const detail = err?.response?.data?.detail;
            setError(detail || err?.message || "Error cargando ítems");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchItems();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [uploadId]);

    const toggle = async (item: ItemRow) => {
        const nextActive = item.is_active === false;
        setSavingId(item.id);
        setError("");
        try {
            const res = await api.patch(`/content/uploads/${uploadId}/items/${item.id}`, {
                is_active: nextActive,
            });
            const updated = res.data;
            setItems((prev) => prev.map((i) => (i.id === updated.id ? updated : i)));
        } catch (err: any) {
            const detail = err?.response?.data?.detail;
            setError(detail || err?.message || "Error actualizando ítem");
        } finally {
            setSavingId(null);
        }
    };

    return (
        <div
            style={{
                position: "fixed",
                inset: 0,
                backgroundColor: "rgba(0,0,0,0.55)",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                padding: "1rem",
                zIndex: 50,
            }}
            onClick={onClose}
        >
            <div
                className="card"
                style={{ maxWidth: "920px", width: "100%", maxHeight: "85vh", overflow: "auto" }}
                onClick={(e) => e.stopPropagation()}
            >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                        <h3 style={{ margin: 0 }}>Ítems del upload</h3>
                        <p style={{ margin: "0.25rem 0 0 0", color: "var(--text-secondary)" }}>
                            Activos: {activeCount} / {items.length}
                        </p>
                    </div>
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                        <button className="btn btn-secondary" onClick={fetchItems} disabled={loading}>
                            {loading ? "Cargando..." : "Refrescar"}
                        </button>
                        <button className="btn" onClick={onClose}>
                            Cerrar
                        </button>
                    </div>
                </div>

                {error && (
                    <p style={{ color: "var(--error)", marginTop: "1rem", fontWeight: 600 }}>{error}</p>
                )}

                {loading ? (
                    <p style={{ marginTop: "1rem" }}>Cargando ítems...</p>
                ) : items.length === 0 ? (
                    <p style={{ marginTop: "1rem" }}>No hay ítems para este upload.</p>
                ) : (
                    <table style={{ width: "100%", borderCollapse: "collapse", marginTop: "1rem" }}>
                        <thead>
                            <tr style={{ textAlign: "left", borderBottom: "1px solid var(--border-color)" }}>
                                <th style={{ padding: "0.5rem" }}>Estado</th>
                                <th style={{ padding: "0.5rem" }}>Tipo</th>
                                <th style={{ padding: "0.5rem" }}>Enunciado</th>
                                <th style={{ padding: "0.5rem", width: "180px" }}>Acción</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items.map((item) => (
                                <tr key={item.id} style={{ borderBottom: "1px solid var(--border-color)" }}>
                                    <td style={{ padding: "0.5rem" }}>
                                        <span
                                            style={{
                                                padding: "0.2rem 0.55rem",
                                                borderRadius: "var(--radius-sm)",
                                                backgroundColor:
                                                    item.is_active === false
                                                        ? "rgba(255,255,255,0.06)"
                                                        : "rgba(46, 204, 113, 0.15)",
                                                color:
                                                    item.is_active === false
                                                        ? "var(--text-secondary)"
                                                        : "var(--success)",
                                                fontWeight: 700,
                                                fontSize: "0.85rem",
                                            }}
                                        >
                                            {item.is_active === false ? "Inactivo" : "Activo"}
                                        </span>
                                    </td>
                                    <td style={{ padding: "0.5rem" }}>{item.type}</td>
                                    <td style={{ padding: "0.5rem" }}>{summarizeStem(item.stem)}</td>
                                    <td style={{ padding: "0.5rem" }}>
                                        <button
                                            className="btn btn-secondary"
                                            disabled={savingId === item.id}
                                            onClick={() => toggle(item)}
                                        >
                                            {savingId === item.id
                                                ? "Guardando..."
                                                : item.is_active === false
                                                    ? "Activar"
                                                    : "Desactivar"}
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}

                <p style={{ marginTop: "1rem", color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                    Los ítems inactivos no se servirán en nuevas sesiones.
                </p>
            </div>
        </div>
    );
}

