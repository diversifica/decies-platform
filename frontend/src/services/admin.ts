"use client";

import api from "./api";

export interface AdminItemSummary {
  id: string;
  content_upload_id: string;
  microconcept_id?: string | null;
  type: string;
  stem: string;
  is_active: boolean;
  created_at?: string | null;
}

export interface AdminRecommendationCatalogEntry {
  code: string;
  title: string;
  description: string;
  category: string;
  active: boolean;
  catalog_version: string;
}

export interface AdminActivityType {
  id: string;
  code: string;
  name: string;
  active: boolean;
  created_at?: string | null;
}

export async function fetchAdminItems(params: {
  limit?: number;
  offset?: number;
  content_upload_id?: string;
  microconcept_id?: string;
  is_active?: boolean;
}): Promise<AdminItemSummary[]> {
  const res = await api.get("/admin/items", { params });
  return res.data as AdminItemSummary[];
}

export async function fetchAdminRecommendationCatalog(params: {
  active?: boolean;
  category?: string;
}): Promise<AdminRecommendationCatalogEntry[]> {
  const res = await api.get("/admin/recommendation-catalog", { params });
  return res.data as AdminRecommendationCatalogEntry[];
}

export async function updateAdminRecommendationCatalog(
  code: string,
  payload: Partial<AdminRecommendationCatalogEntry>,
): Promise<AdminRecommendationCatalogEntry> {
  const res = await api.patch(`/admin/recommendation-catalog/${code}`, payload);
  return res.data as AdminRecommendationCatalogEntry;
}

export async function fetchAdminActivityTypes(params: {
  active?: boolean;
}): Promise<AdminActivityType[]> {
  const res = await api.get("/admin/activity-types", { params });
  return res.data as AdminActivityType[];
}

export async function updateAdminActivityType(
  activityTypeId: string,
  payload: { name?: string; active?: boolean },
): Promise<AdminActivityType> {
  const res = await api.patch(`/admin/activity-types/${activityTypeId}`, payload);
  return res.data as AdminActivityType;
}

export interface AdminGame {
  code: string;
  name: string;
  item_type: string;
  active: boolean;
  has_content: boolean;
  last_processed_at: string | null;
  prompt_version: string;
  engine_version: string;
}

export async function fetchAdminGames(): Promise<AdminGame[]> {
  const res = await api.get("/admin/games");
  return res.data as AdminGame[];
}

export async function updateAdminGame(
  code: string,
  payload: { active?: boolean },
): Promise<AdminGame> {
  const res = await api.patch(`/admin/games/${code}`, payload);
  return res.data as AdminGame;
}

