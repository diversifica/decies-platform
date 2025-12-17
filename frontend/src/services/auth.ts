"use client";

import api, { ACCESS_TOKEN_STORAGE_KEY } from './api';

export interface AuthMe {
    id: string;
    email: string;
    full_name?: string | null;
    role?: string | null;
    tutor_id?: string | null;
    student_id?: string | null;
}

export function getAccessToken(): string | null {
    if (typeof window === 'undefined') return null;
    return window.localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);
}

export function setAccessToken(token: string) {
    window.localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, token);
}

export function clearAccessToken() {
    window.localStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY);
}

export async function login(email: string, password: string): Promise<string> {
    const res = await api.post('/login/access-token', { email, password });
    return res.data.access_token as string;
}

export async function fetchMe(): Promise<AuthMe> {
    const res = await api.get('/auth/me');
    return res.data as AuthMe;
}

