import axios, { AxiosHeaders } from 'axios';

export const ACCESS_TOKEN_STORAGE_KEY = 'decies.access_token';

const api = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },
});

api.interceptors.request.use((config) => {
    if (typeof window !== 'undefined') {
        const token = window.localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);
        if (token) {
            const headers = AxiosHeaders.from(config.headers ?? {});
            headers.set('Authorization', `Bearer ${token}`);
            config.headers = headers;
        }
    }
    return config;
});

export default api;
