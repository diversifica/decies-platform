import api from "./api";

export interface MicroConcept {
    id: string;
    subject_id: string;
    term_id: string | null;
    topic_id: string | null;
    code: string | null;
    name: string;
    description: string | null;
    active: boolean;
    created_at: string | null;
    updated_at: string | null;
}

export interface MicroConceptCreatePayload {
    subject_id: string;
    term_id: string | null;
    topic_id?: string | null;
    code?: string | null;
    name: string;
    description?: string | null;
    active?: boolean;
}

export type MicroConceptUpdatePayload = Partial<
    Pick<MicroConcept, "term_id" | "topic_id" | "code" | "name" | "description" | "active">
>;

export async function fetchMicroconcepts(params: {
    subjectId: string;
    termId?: string;
    active?: boolean;
}): Promise<MicroConcept[]> {
    const res = await api.get(`/microconcepts/subjects/${params.subjectId}`, {
        params: {
            term_id: params.termId,
            active: params.active,
        },
    });
    return res.data;
}

export async function createMicroconcept(payload: MicroConceptCreatePayload): Promise<MicroConcept> {
    const res = await api.post("/microconcepts", payload);
    return res.data;
}

export async function updateMicroconcept(
    microconceptId: string,
    payload: MicroConceptUpdatePayload
): Promise<MicroConcept> {
    const res = await api.patch(`/microconcepts/${microconceptId}`, payload);
    return res.data;
}

