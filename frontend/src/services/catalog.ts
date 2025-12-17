"use client";

import api from './api';

export interface SubjectSummary {
    id: string;
    name: string;
    description?: string | null;
}

export interface TermSummary {
    id: string;
    code: string;
    name: string;
    status: string;
}

export interface StudentSummary {
    id: string;
    user_id?: string | null;
    subject_id?: string | null;
    email?: string | null;
    full_name?: string | null;
}

export async function fetchSubjects(mine = true): Promise<SubjectSummary[]> {
    const res = await api.get('/catalog/subjects', { params: { mine } });
    return res.data as SubjectSummary[];
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

