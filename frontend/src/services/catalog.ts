"use client";

import api from './api';

export interface SubjectSummary {
    id: string;
    name: string;
    description?: string | null;
}

export interface SubjectCreatePayload {
    name: string;
    description?: string | null;
}

export interface SubjectUpdatePayload {
    name?: string;
    description?: string | null;
}

export interface TermSummary {
    id: string;
    code: string;
    name: string;
    status: string;
    academic_year_name?: string | null;
}

export interface StudentSummary {
    id: string;
    user_id?: string | null;
    subject_id?: string | null;
    email?: string | null;
    full_name?: string | null;
}

export interface TopicSummary {
    id: string;
    subject_id: string;
    term_id?: string | null;
    code?: string | null;
    name: string;
}

export async function fetchSubjects(mine = true): Promise<SubjectSummary[]> {
    const res = await api.get('/catalog/subjects', { params: { mine } });
    return res.data as SubjectSummary[];
}

export async function createSubject(payload: SubjectCreatePayload): Promise<SubjectSummary> {
    const res = await api.post('/catalog/subjects', payload);
    return res.data as SubjectSummary;
}

export async function updateSubject(
    subjectId: string,
    payload: SubjectUpdatePayload,
): Promise<SubjectSummary> {
    const res = await api.put(`/catalog/subjects/${subjectId}`, payload);
    return res.data as SubjectSummary;
}

export async function deleteSubject(subjectId: string): Promise<void> {
    await api.delete(`/catalog/subjects/${subjectId}?force=true`);
}

export async function assignStudentSubject(studentId: string, subjectId: string): Promise<StudentSummary> {
    const res = await api.patch(`/catalog/students/${studentId}`, { subject_id: subjectId });
    return res.data as StudentSummary;
}

export async function fetchTerms(active: boolean | null = true): Promise<TermSummary[]> {
    const res = await api.get('/catalog/terms', { params: { active } });
    return res.data as TermSummary[];
}

export async function fetchStudents(mine = true, subjectId?: string): Promise<StudentSummary[]> {
    const res = await api.get('/catalog/students', {
        params: { mine, subject_id: subjectId },
    });
    return res.data as StudentSummary[];
}

export async function fetchTopics(params: {
    mine?: boolean;
    subjectId?: string;
    termId?: string;
}): Promise<TopicSummary[]> {
    const res = await api.get('/catalog/topics', {
        params: {
            mine: params.mine ?? true,
            subject_id: params.subjectId,
            term_id: params.termId,
        },
    });
    return res.data as TopicSummary[];
}
