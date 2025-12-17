"use client";

import { useState } from 'react';
import UploadForm from '../../components/tutor/UploadForm';
import UploadList from '../../components/tutor/UploadList';
import MetricsDashboard from '../../components/tutor/MetricsDashboard';

export default function TutorPage() {
    const [activeTab, setActiveTab] = useState<'content' | 'metrics'>('content');

    // Hardcoded for MVP - from seed.py output
    const STUDENT_ID = "b3a2f673-4411-41bd-bf4b-f31211d90050";
    const SUBJECT_ID = "e13cc7df-4a91-48b8-a1ef-e235cff9689d";
    const TERM_ID = "3141b86d-162d-49b7-b34e-7c19218aa464";

    return (
        <div>
            <h2 style={{ marginBottom: '2rem', textAlign: 'center' }}>Panel del Tutor</h2>

            {/* Tabs */}
            <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem', borderBottom: '2px solid var(--border-color)' }}>
                <button
                    onClick={() => setActiveTab('content')}
                    style={{
                        padding: '0.75rem 1.5rem',
                        background: 'none',
                        border: 'none',
                        borderBottom: activeTab === 'content' ? '2px solid var(--primary)' : '2px solid transparent',
                        color: activeTab === 'content' ? 'var(--primary)' : 'var(--text-secondary)',
                        fontWeight: activeTab === 'content' ? 'bold' : 'normal',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                        marginBottom: '-2px'
                    }}
                >
                    Contenido
                </button>
                <button
                    onClick={() => setActiveTab('metrics')}
                    style={{
                        padding: '0.75rem 1.5rem',
                        background: 'none',
                        border: 'none',
                        borderBottom: activeTab === 'metrics' ? '2px solid var(--primary)' : '2px solid transparent',
                        color: activeTab === 'metrics' ? 'var(--primary)' : 'var(--text-secondary)',
                        fontWeight: activeTab === 'metrics' ? 'bold' : 'normal',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                        marginBottom: '-2px'
                    }}
                >
                    Métricas y Dominio
                </button>
            </div>

            {/* Content */}
            {activeTab === 'content' ? (
                <div style={{ display: 'grid', gap: '2rem' }}>
                    <section>
                        <UploadForm />
                    </section>

                    <section>
                        <UploadList />
                    </section>
                </div>
            ) : (
                <MetricsDashboard
                    studentId={STUDENT_ID}
                    subjectId={SUBJECT_ID}
                    termId={TERM_ID}
                />
            )}
        </div>
    );
}
