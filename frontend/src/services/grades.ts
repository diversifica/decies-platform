import api from "./api";

export interface AssessmentScopeTag {
    id: string;
    real_grade_id: string;
    topic_id: string | null;
    microconcept_id: string | null;
    weight: number | null;
}

export interface RealGrade {
    id: string;
    student_id: string;
    subject_id: string;
    term_id: string;
    assessment_date: string; // YYYY-MM-DD
    grade_value: number;
    grading_scale: string | null;
    notes: string | null;
    created_by_tutor_id: string;
    created_at: string | null;
    scope_tags: AssessmentScopeTag[];
}

export interface AssessmentScopeTagCreatePayload {
    topic_id?: string | null;
    microconcept_id?: string | null;
    weight?: number | null;
}

export interface RealGradeCreatePayload {
    student_id: string;
    subject_id: string;
    term_id: string;
    assessment_date: string;
    grade_value: number;
    grading_scale?: string | null;
    notes?: string | null;
    scope_tags?: AssessmentScopeTagCreatePayload[];
}

export type RealGradeUpdatePayload = Partial<
    Pick<RealGrade, "assessment_date" | "grade_value" | "grading_scale" | "notes">
>;

export async function fetchGrades(params: {
    studentId?: string;
    subjectId?: string;
    termId?: string;
    limit?: number;
}): Promise<RealGrade[]> {
    const res = await api.get("/grades", {
        params: {
            student_id: params.studentId,
            subject_id: params.subjectId,
            term_id: params.termId,
            limit: params.limit ?? 50,
        },
    });
    return res.data as RealGrade[];
}

export async function createGrade(payload: RealGradeCreatePayload): Promise<RealGrade> {
    const res = await api.post("/grades", payload);
    return res.data as RealGrade;
}

export async function updateGrade(gradeId: string, payload: RealGradeUpdatePayload): Promise<RealGrade> {
    const res = await api.patch(`/grades/${gradeId}`, payload);
    return res.data as RealGrade;
}

export async function deleteGrade(gradeId: string): Promise<void> {
    await api.delete(`/grades/${gradeId}`);
}

export async function addGradeTag(
    gradeId: string,
    payload: AssessmentScopeTagCreatePayload
): Promise<AssessmentScopeTag> {
    const res = await api.post(`/grades/${gradeId}/tags`, payload);
    return res.data as AssessmentScopeTag;
}

export async function deleteGradeTag(gradeId: string, tagId: string): Promise<void> {
    await api.delete(`/grades/${gradeId}/tags/${tagId}`);
}

