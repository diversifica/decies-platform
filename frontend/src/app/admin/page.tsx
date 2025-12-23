"use client";

import { Fragment, useEffect, useMemo, useState } from "react";

import AuthPanel from "../../components/auth/AuthPanel";
import { AuthMe } from "../../services/auth";
import {
  AdminActivityType,
  AdminGame,
  AdminItemSummary,
  AdminRecommendationCatalogEntry,
  fetchAdminActivityTypes,
  fetchAdminGames,
  fetchAdminItems,
  fetchAdminRecommendationCatalog,
  updateAdminActivityType,
  updateAdminGame,
  updateAdminRecommendationCatalog,
} from "../../services/admin";

type AdminTab = "items" | "catalog" | "activityTypes" | "games";

function formatDate(value?: string | null): string {
  if (!value) return "";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

function truncate(value: string, max = 140): string {
  if (!value) return "";
  if (value.length <= max) return value;
  return `${value.slice(0, max)}…`;
}

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<AdminTab>("items");
  const [me, setMe] = useState<AuthMe | null>(null);

  const isAdmin = useMemo(
    () => (me?.role || "").toLowerCase() === "admin",
    [me?.role],
  );

  const tabStyle = (tab: AdminTab) => ({
    padding: "0.75rem 1.25rem",
    background: "none",
    border: "none",
    borderBottom:
      activeTab === tab
        ? "2px solid var(--accent-primary)"
        : "2px solid transparent",
    color: activeTab === tab ? "var(--accent-primary)" : "var(--text-secondary)",
    fontWeight: activeTab === tab ? ("bold" as const) : ("normal" as const),
    cursor: "pointer",
    transition: "all 0.2s ease",
    marginBottom: "-2px",
  });

  return (
    <div>
      <h2 style={{ marginBottom: "2rem", textAlign: "center" }}>Panel Admin</h2>

      <AuthPanel
        title="Acceso Admin"
        defaultEmail="admin@decies.com"
        defaultPassword="decies"
        onAuth={(loadedMe) => setMe(loadedMe)}
        onLogout={() => setMe(null)}
      />

      {me && !isAdmin && (
        <div
          className="card"
          style={{
            marginBottom: "1.5rem",
            borderLeft: "4px solid var(--error)",
          }}
        >
          <h3 style={{ marginBottom: "0.5rem" }}>Acceso restringido</h3>
          <p style={{ margin: 0 }}>
            Has iniciado sesión como{" "}
            <strong>{(me.role || "N/A").toUpperCase()}</strong>. Para usar el
            panel admin, inicia sesión con un usuario admin.
          </p>
        </div>
      )}

      {isAdmin && (
        <>
          <div
            className="card"
            style={{ marginBottom: "1.5rem", padding: "0.75rem 1rem" }}
          >
            <div
              style={{
                display: "flex",
                gap: "0.5rem",
                borderBottom: "1px solid var(--border-color)",
                marginBottom: "0.75rem",
              }}
            >
              <button style={tabStyle("items")} onClick={() => setActiveTab("items")}>
                Ítems
              </button>
              <button
                style={tabStyle("catalog")}
                onClick={() => setActiveTab("catalog")}
              >
                Recommendation Catalog
              </button>
              <button
                style={tabStyle("activityTypes")}
                onClick={() => setActiveTab("activityTypes")}
              >
                Activity Types
              </button>
              <button
                style={tabStyle("games")}
                onClick={() => setActiveTab("games")}
              >
                Juegos
              </button>
            </div>

            {activeTab === "items" && <AdminItemsPanel />}
            {activeTab === "catalog" && <AdminCatalogPanel />}
            {activeTab === "activityTypes" && <AdminActivityTypesPanel />}
            {activeTab === "games" && <AdminGamesPanel />}
          </div>
        </>
      )}
    </div>
  );
}

function AdminItemsPanel() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [items, setItems] = useState<AdminItemSummary[]>([]);

  const [contentUploadId, setContentUploadId] = useState("");
  const [microconceptId, setMicroconceptId] = useState("");
  const [isActive, setIsActive] = useState<"all" | "true" | "false">("all");
  const [limit, setLimit] = useState(50);

  const load = async () => {
    setError("");
    setLoading(true);
    try {
      const params: Parameters<typeof fetchAdminItems>[0] = {
        limit,
        offset: 0,
      };
      if (contentUploadId.trim()) params.content_upload_id = contentUploadId.trim();
      if (microconceptId.trim()) params.microconcept_id = microconceptId.trim();
      if (isActive !== "all") params.is_active = isActive === "true";
      const data = await fetchAdminItems(params);
      setItems(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Error cargando ítems");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "1rem",
          marginBottom: "1rem",
        }}
      >
        <label>
          Content Upload ID
          <input
            className="input"
            value={contentUploadId}
            onChange={(e) => setContentUploadId(e.target.value)}
            placeholder="uuid"
          />
        </label>
        <label>
          Microconcept ID
          <input
            className="input"
            value={microconceptId}
            onChange={(e) => setMicroconceptId(e.target.value)}
            placeholder="uuid"
          />
        </label>
        <label>
          Activo
          <select
            className="input"
            value={isActive}
            onChange={(e) => setIsActive(e.target.value as "all" | "true" | "false")}
          >
            <option value="all">Todos</option>
            <option value="true">Sí</option>
            <option value="false">No</option>
          </select>
        </label>
        <label>
          Límite
          <input
            className="input"
            type="number"
            value={limit}
            min={1}
            max={200}
            onChange={(e) => setLimit(Number(e.target.value || 50))}
          />
        </label>
      </div>

      <div style={{ display: "flex", gap: "0.75rem", marginBottom: "1rem" }}>
        <button className="btn" onClick={load} disabled={loading}>
          {loading ? "Cargando…" : "Buscar"}
        </button>
      </div>

      {error && <div style={{ color: "var(--error)", marginBottom: "1rem" }}>{error}</div>}

      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ textAlign: "left", borderBottom: "1px solid var(--border-color)" }}>
              <th style={{ padding: "0.5rem" }}>Tipo</th>
              <th style={{ padding: "0.5rem" }}>Activo</th>
              <th style={{ padding: "0.5rem" }}>Stem</th>
              <th style={{ padding: "0.5rem" }}>Content</th>
              <th style={{ padding: "0.5rem" }}>Microconcept</th>
              <th style={{ padding: "0.5rem" }}>Creado</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr
                key={item.id}
                style={{ borderBottom: "1px solid var(--border-color)" }}
              >
                <td style={{ padding: "0.5rem", whiteSpace: "nowrap" }}>{item.type}</td>
                <td style={{ padding: "0.5rem", whiteSpace: "nowrap" }}>
                  {item.is_active ? "Sí" : "No"}
                </td>
                <td style={{ padding: "0.5rem" }}>{truncate(item.stem)}</td>
                <td style={{ padding: "0.5rem", fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                  {item.content_upload_id}
                </td>
                <td style={{ padding: "0.5rem", fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                  {item.microconcept_id || "—"}
                </td>
                <td style={{ padding: "0.5rem", whiteSpace: "nowrap", color: "var(--text-secondary)" }}>
                  {formatDate(item.created_at)}
                </td>
              </tr>
            ))}
            {!loading && items.length === 0 && (
              <tr>
                <td colSpan={6} style={{ padding: "0.75rem", color: "var(--text-secondary)" }}>
                  No hay ítems para los filtros actuales.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function AdminCatalogPanel() {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [rows, setRows] = useState<AdminRecommendationCatalogEntry[]>([]);

  const [active, setActive] = useState<"all" | "true" | "false">("all");
  const [category, setCategory] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);

  const [edit, setEdit] = useState<
    Record<
      string,
      Partial<Pick<AdminRecommendationCatalogEntry, "title" | "description" | "category" | "active" | "catalog_version">>
    >
  >({});

  const load = async () => {
    setError("");
    setLoading(true);
    try {
      const params: Parameters<typeof fetchAdminRecommendationCatalog>[0] = {};
      if (active !== "all") params.active = active === "true";
      if (category.trim()) params.category = category.trim();
      const data = await fetchAdminRecommendationCatalog(params);
      setRows(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Error cargando catálogo");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const startEdit = (row: AdminRecommendationCatalogEntry) => {
    setExpanded(row.code);
    setEdit((prev) => ({
      ...prev,
      [row.code]: {
        title: row.title,
        description: row.description,
        category: row.category,
        active: row.active,
        catalog_version: row.catalog_version,
      },
    }));
  };

  const save = async (code: string) => {
    const payload = edit[code] || {};
    setSaving(code);
    setError("");
    try {
      await updateAdminRecommendationCatalog(code, payload);
      await load();
      setExpanded(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Error guardando cambios");
    } finally {
      setSaving(null);
    }
  };

  return (
    <div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "1rem",
          marginBottom: "1rem",
        }}
      >
        <label>
          Activo
          <select
            className="input"
            value={active}
            onChange={(e) => setActive(e.target.value as "all" | "true" | "false")}
          >
            <option value="all">Todos</option>
            <option value="true">Sí</option>
            <option value="false">No</option>
          </select>
        </label>
        <label>
          Categoría
          <input
            className="input"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            placeholder="focus / strategy / dosage / external_validation"
          />
        </label>
      </div>

      <div style={{ display: "flex", gap: "0.75rem", marginBottom: "1rem" }}>
        <button className="btn" onClick={load} disabled={loading}>
          {loading ? "Cargando…" : "Filtrar"}
        </button>
      </div>

      {error && <div style={{ color: "var(--error)", marginBottom: "1rem" }}>{error}</div>}

      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ textAlign: "left", borderBottom: "1px solid var(--border-color)" }}>
              <th style={{ padding: "0.5rem" }}>Código</th>
              <th style={{ padding: "0.5rem" }}>Título</th>
              <th style={{ padding: "0.5rem" }}>Categoría</th>
              <th style={{ padding: "0.5rem" }}>Activo</th>
              <th style={{ padding: "0.5rem" }}>Versión</th>
              <th style={{ padding: "0.5rem" }} />
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const isOpen = expanded === row.code;
              const current = edit[row.code] || {};
              return (
                <Fragment key={row.code}>
                  <tr
                    style={{ borderBottom: "1px solid var(--border-color)" }}
                  >
                    <td style={{ padding: "0.5rem", whiteSpace: "nowrap" }}>{row.code}</td>
                    <td style={{ padding: "0.5rem" }}>{row.title}</td>
                    <td style={{ padding: "0.5rem", whiteSpace: "nowrap" }}>{row.category}</td>
                    <td style={{ padding: "0.5rem", whiteSpace: "nowrap" }}>
                      {row.active ? "Sí" : "No"}
                    </td>
                    <td style={{ padding: "0.5rem", whiteSpace: "nowrap" }}>
                      {row.catalog_version}
                    </td>
                    <td style={{ padding: "0.5rem", whiteSpace: "nowrap", textAlign: "right" }}>
                      {!isOpen ? (
                        <button className="btn btn-secondary" onClick={() => startEdit(row)}>
                          Editar
                        </button>
                      ) : (
                        <button className="btn btn-secondary" onClick={() => setExpanded(null)}>
                          Cerrar
                        </button>
                      )}
                    </td>
                  </tr>

                  {isOpen && (
                    <tr
                      style={{
                        borderBottom: "1px solid var(--border-color)",
                      }}
                    >
                      <td colSpan={6} style={{ padding: "0.75rem" }}>
                        <div
                          style={{
                            display: "grid",
                            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                            gap: "1rem",
                            marginBottom: "1rem",
                          }}
                        >
                          <label>
                            Título
                            <input
                              className="input"
                              value={current.title ?? ""}
                              onChange={(e) =>
                                setEdit((prev) => ({
                                  ...prev,
                                  [row.code]: { ...prev[row.code], title: e.target.value },
                                }))
                              }
                            />
                          </label>
                          <label>
                            Categoría
                            <input
                              className="input"
                              value={current.category ?? ""}
                              onChange={(e) =>
                                setEdit((prev) => ({
                                  ...prev,
                                  [row.code]: { ...prev[row.code], category: e.target.value },
                                }))
                              }
                            />
                          </label>
                          <label>
                            Activo
                            <select
                              className="input"
                              value={String(current.active ?? row.active)}
                              onChange={(e) =>
                                setEdit((prev) => ({
                                  ...prev,
                                  [row.code]: {
                                    ...prev[row.code],
                                    active: e.target.value === "true",
                                  },
                                }))
                              }
                            >
                              <option value="true">Sí</option>
                              <option value="false">No</option>
                            </select>
                          </label>
                          <label>
                            Versión
                            <input
                              className="input"
                              value={current.catalog_version ?? ""}
                              onChange={(e) =>
                                setEdit((prev) => ({
                                  ...prev,
                                  [row.code]: {
                                    ...prev[row.code],
                                    catalog_version: e.target.value,
                                  },
                                }))
                              }
                            />
                          </label>
                          <label style={{ gridColumn: "1 / -1" }}>
                            Descripción
                            <textarea
                              className="input"
                              style={{ minHeight: "96px" }}
                              value={current.description ?? ""}
                              onChange={(e) =>
                                setEdit((prev) => ({
                                  ...prev,
                                  [row.code]: { ...prev[row.code], description: e.target.value },
                                }))
                              }
                            />
                          </label>
                        </div>

                        <div style={{ display: "flex", gap: "0.75rem" }}>
                          <button
                            className="btn"
                            onClick={() => save(row.code)}
                            disabled={saving === row.code}
                          >
                            {saving === row.code ? "Guardando…" : "Guardar"}
                          </button>
                          <button
                            className="btn btn-secondary"
                            onClick={() => setExpanded(null)}
                          >
                            Cancelar
                          </button>
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
            {!loading && rows.length === 0 && (
              <tr>
                <td colSpan={6} style={{ padding: "0.75rem", color: "var(--text-secondary)" }}>
                  No hay entradas para los filtros actuales.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function AdminActivityTypesPanel() {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [rows, setRows] = useState<AdminActivityType[]>([]);

  const [active, setActive] = useState<"all" | "true" | "false">("all");

  const load = async () => {
    setError("");
    setLoading(true);
    try {
      const params: Parameters<typeof fetchAdminActivityTypes>[0] = {};
      if (active !== "all") params.active = active === "true";
      const data = await fetchAdminActivityTypes(params);
      setRows(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Error cargando activity types");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const patchRow = async (id: string, payload: { name?: string; active?: boolean }) => {
    setSaving(id);
    setError("");
    try {
      await updateAdminActivityType(id, payload);
      await load();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Error guardando cambios");
    } finally {
      setSaving(null);
    }
  };

  return (
    <div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "1rem",
          marginBottom: "1rem",
        }}
      >
        <label>
          Activo
          <select
            className="input"
            value={active}
            onChange={(e) => setActive(e.target.value as "all" | "true" | "false")}
          >
            <option value="all">Todos</option>
            <option value="true">Sí</option>
            <option value="false">No</option>
          </select>
        </label>
      </div>

      <div style={{ display: "flex", gap: "0.75rem", marginBottom: "1rem" }}>
        <button className="btn" onClick={load} disabled={loading}>
          {loading ? "Cargando…" : "Refrescar"}
        </button>
      </div>

      {error && <div style={{ color: "var(--error)", marginBottom: "1rem" }}>{error}</div>}

      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ textAlign: "left", borderBottom: "1px solid var(--border-color)" }}>
              <th style={{ padding: "0.5rem" }}>Código</th>
              <th style={{ padding: "0.5rem" }}>Nombre</th>
              <th style={{ padding: "0.5rem" }}>Activo</th>
              <th style={{ padding: "0.5rem" }} />
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} style={{ borderBottom: "1px solid var(--border-color)" }}>
                <td style={{ padding: "0.5rem", whiteSpace: "nowrap" }}>{row.code}</td>
                <td style={{ padding: "0.5rem" }}>
                  <input
                    className="input"
                    value={row.name}
                    onChange={(e) =>
                      setRows((prev) =>
                        prev.map((r) => (r.id === row.id ? { ...r, name: e.target.value } : r)),
                      )
                    }
                  />
                </td>
                <td style={{ padding: "0.5rem", whiteSpace: "nowrap" }}>
                  <select
                    className="input"
                    value={String(row.active)}
                    onChange={(e) =>
                      setRows((prev) =>
                        prev.map((r) =>
                          r.id === row.id ? { ...r, active: e.target.value === "true" } : r,
                        ),
                      )
                    }
                  >
                    <option value="true">Sí</option>
                    <option value="false">No</option>
                  </select>
                </td>
                <td style={{ padding: "0.5rem", whiteSpace: "nowrap", textAlign: "right" }}>
                  <button
                    className="btn btn-secondary"
                    disabled={saving === row.id}
                    onClick={() => patchRow(row.id, { name: row.name, active: row.active })}
                  >
                    {saving === row.id ? "Guardando…" : "Guardar"}
                  </button>
                </td>
              </tr>
            ))}
            {!loading && rows.length === 0 && (
              <tr>
                <td colSpan={4} style={{ padding: "0.75rem", color: "var(--text-secondary)" }}>
                  No hay activity types para los filtros actuales.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function AdminGamesPanel() {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [games, setGames] = useState<AdminGame[]>([]);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [pendingToggle, setPendingToggle] = useState<{
    code: string;
    name: string;
    active: boolean;
  } | null>(null);

  const load = async () => {
    setError("");
    setLoading(true);
    try {
      const data = await fetchAdminGames();
      setGames(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Error cargando juegos");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const patchGame = async (code: string, payload: { active: boolean }) => {
    setSaving(code);
    setError("");
    try {
      await updateAdminGame(code, payload);
      await load();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Error guardando cambios");
    } finally {
      setSaving(null);
    }
  };

  const handleToggle = (game: AdminGame) => {
    // Si se está desactivando, no hay problema
    if (game.active) {
      patchGame(game.code, { active: false });
      return;
    }

    // Si se está activando y no tiene contenido, mostrar modal
    if (!game.has_content) {
      setPendingToggle({ code: game.code, name: game.name, active: true });
      setShowConfirmModal(true);
      return;
    }

    // Si tiene contenido, activar directamente
    patchGame(game.code, { active: true });
  };

  const confirmToggle = () => {
    if (pendingToggle) {
      patchGame(pendingToggle.code, { active: pendingToggle.active });
    }
    setShowConfirmModal(false);
    setPendingToggle(null);
  };

  const cancelToggle = () => {
    setShowConfirmModal(false);
    setPendingToggle(null);
  };

  return (
    <div>
      <div style={{ display: "flex", gap: "0.75rem", marginBottom: "1rem" }}>
        <button className="btn" onClick={load} disabled={loading}>
          {loading ? "Cargando…" : "Refrescar"}
        </button>
      </div>

      {error && <div style={{ color: "var(--error)", marginBottom: "1rem" }}>{error}</div>}

      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ textAlign: "left", borderBottom: "1px solid var(--border-color)" }}>
              <th style={{ padding: "0.5rem" }}>Código</th>
              <th style={{ padding: "0.5rem" }}>Nombre</th>
              <th style={{ padding: "0.5rem" }}>Tipo</th>
              <th style={{ padding: "0.5rem" }}>Activo</th>
              <th style={{ padding: "0.5rem" }}>Contenido</th>
              <th style={{ padding: "0.5rem" }}>Última Generación</th>
              <th style={{ padding: "0.5rem" }}>Versiones</th>
            </tr>
          </thead>
          <tbody>
            {games.map((game) => (
              <tr key={game.code} style={{ borderBottom: "1px solid var(--border-color)" }}>
                <td style={{ padding: "0.5rem", whiteSpace: "nowrap" }}>{game.code}</td>
                <td style={{ padding: "0.5rem" }}>{game.name}</td>
                <td style={{ padding: "0.5rem", whiteSpace: "nowrap" }}>{game.item_type}</td>
                <td style={{ padding: "0.5rem", whiteSpace: "nowrap" }}>
                  <select
                    className="input"
                    value={String(game.active)}
                    onChange={() => handleToggle(game)}
                    disabled={saving === game.code}
                    style={{ minWidth: "80px" }}
                  >
                    <option value="true">Sí</option>
                    <option value="false">No</option>
                  </select>
                </td>
                <td style={{ padding: "0.5rem", whiteSpace: "nowrap", textAlign: "center" }}>
                  {game.has_content ? (
                    <span style={{ color: "var(--success)", fontSize: "1.2rem" }}>✓</span>
                  ) : (
                    <span style={{ color: "var(--warning)", fontSize: "1.2rem" }}>⚠</span>
                  )}
                </td>
                <td style={{ padding: "0.5rem", whiteSpace: "nowrap", color: "var(--text-secondary)" }}>
                  {game.last_processed_at ? formatDate(game.last_processed_at) : "Nunca"}
                </td>
                <td style={{ padding: "0.5rem", fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                  P:{game.prompt_version} / E:{game.engine_version}
                </td>
              </tr>
            ))}
            {!loading && games.length === 0 && (
              <tr>
                <td colSpan={7} style={{ padding: "0.75rem", color: "var(--text-secondary)" }}>
                  No hay juegos disponibles.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Modal de confirmación */}
      {showConfirmModal && pendingToggle && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
          }}
          onClick={cancelToggle}
        >
          <div
            className="card"
            style={{
              maxWidth: "500px",
              padding: "1.5rem",
              borderLeft: "4px solid var(--warning)",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ marginBottom: "1rem" }}>⚠ Advertencia</h3>
            <p style={{ marginBottom: "1rem" }}>
              El juego <strong>{pendingToggle.name}</strong> no tiene contenido generado aún.
              Si lo activas, se generarán ítems en el próximo procesamiento de contenido.
            </p>
            <p style={{ marginBottom: "1.5rem", color: "var(--text-secondary)" }}>
              ¿Estás seguro de que deseas activar este juego?
            </p>
            <div style={{ display: "flex", gap: "0.75rem", justifyContent: "flex-end" }}>
              <button className="btn btn-secondary" onClick={cancelToggle}>
                Cancelar
              </button>
              <button className="btn" onClick={confirmToggle}>
                Activar de todas formas
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
