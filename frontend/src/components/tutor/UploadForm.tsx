"use client";

import { useEffect, useState } from 'react';
import api from '../../services/api';

interface UploadFormProps {
    subjectId?: string;
    termId?: string;
    onUploadSuccess?: () => void;
}

export default function UploadForm({ subjectId: subjectIdProp = '', termId: termIdProp = '', onUploadSuccess }: UploadFormProps) {
    const [file, setFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');

    const [subjectId, setSubjectId] = useState(subjectIdProp);
    const [termId, setTermId] = useState(termIdProp);

    useEffect(() => setSubjectId(subjectIdProp), [subjectIdProp]);
    useEffect(() => setTermId(termIdProp), [termIdProp]);

    const handleUpload = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!file || !subjectId || !termId) {
            setMessage("Por favor completa todos los campos");
            return;
        }

        setLoading(true);
        setMessage('');

        const formData = new FormData();
        formData.append('file', file);
        formData.append('subject_id', subjectId);
        formData.append('term_id', termId);
        // Defaults
        formData.append('upload_type', 'pdf');

        try {
            const res = await api.post('/content/uploads', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setMessage(`Subida exitosa: ID ${res.data.id}`);
            setFile(null);
            onUploadSuccess?.();
        } catch (error: any) {
            console.error(error);
            const detail = error.response?.data?.detail;
            if (detail === 'Not enough permissions') {
                setMessage('Error: necesitas iniciar sesión como tutor.');
            } else {
                setMessage(`Error: ${detail || error.message}`);
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="card" style={{ maxWidth: '500px', margin: '0 auto' }}>
            <h3 style={{ marginBottom: '1rem' }}>Subir Nuevo Contenido</h3>
            <form onSubmit={handleUpload} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>

                <label>
                    Archivo (PDF)
                    <input
                        type="file"
                        accept=".pdf"
                        onChange={(e) => setFile(e.target.files?.[0] || null)}
                        className="input"
                    />
                </label>

                <label>
                    Subject ID
                    <input
                        type="text"
                        value={subjectId}
                        onChange={e => setSubjectId(e.target.value)}
                        placeholder="UUID..."
                        className="input"
                        disabled={!!subjectIdProp}
                    />
                </label>

                <label>
                    Term ID
                    <input
                        type="text"
                        value={termId}
                        onChange={e => setTermId(e.target.value)}
                        placeholder="UUID..."
                        className="input"
                        disabled={!!termIdProp}
                    />
                </label>

                <button type="submit" disabled={loading} className="btn">
                    {loading ? 'Subiendo...' : 'Subir PDF'}
                </button>

                {message && (
                    <p style={{
                        color: message.startsWith('Error') ? 'var(--error)' : 'var(--success)',
                        marginTop: '1rem'
                    }}>
                        {message}
                    </p>
                )}
            </form>
        </div>
    );
}
