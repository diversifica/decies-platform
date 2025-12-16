"use client";

import { useState } from 'react';
import api from '../../services/api';

export default function UploadForm() {
    const [file, setFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');

    // Preliminary hardcoded IDs or inputs - For MVP Day 3 we assume user knows them or we default
    // Ideally these come from Auth context or Dropdowns
    const [tutorId, setTutorId] = useState('');
    const [subjectId, setSubjectId] = useState('');
    const [termId, setTermId] = useState('');

    const handleUpload = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!file || !tutorId || !subjectId || !termId) {
            setMessage("Por favor completa todos los campos");
            return;
        }

        setLoading(true);
        setMessage('');

        const formData = new FormData();
        formData.append('file', file);
        formData.append('tutor_id', tutorId);
        formData.append('subject_id', subjectId);
        formData.append('term_id', termId);
        // Defaults
        formData.append('upload_type', 'pdf');
        formData.append('page_count', '1');

        try {
            const res = await api.post('/content/uploads/', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setMessage(`Subida exitosa: ID ${res.data.id}`);
            setFile(null);
            // Trigger refresh?
        } catch (error: any) {
            console.error(error);
            setMessage(`Error: ${error.response?.data?.detail || error.message}`);
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
                    Tutor ID
                    <input
                        type="text"
                        value={tutorId}
                        onChange={e => setTutorId(e.target.value)}
                        placeholder="UUID..."
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
