"use client";

import { useState } from 'react';
import UploadForm from '../../components/tutor/UploadForm';
import UploadList from '../../components/tutor/UploadList';
import MetricsDashboard from '../../components/tutor/MetricsDashboard';
import RecommendationList from '../../components/tutor/RecommendationList';

export default function TutorPage() {
    const [activeTab, setActiveTab] = useState<'content' | 'metrics' | 'recommendations'>('content');

    // Hardcoded for MVP - from seed.py output
    const TUTOR_ID = "a2c1b4e5-9876-4321-abcd-1234567890ab"; // Default Tuthill
    const STUDENT_ID = "b3a2f673-4411-41bd-bf4b-f31211d90050";
    const SUBJECT_ID = "e13cc7df-4a91-48b8-a1ef-e235cff9689d";
    const TERM_ID = "3141b86d-162d-49b7-b34e-7c19218aa464";

    const getTabStyle = (tabName: string) => ({
        padding: '0.75rem 1.5rem',
        background: 'none',
        border: 'none',
        borderBottom: activeTab === tabName ? '2px solid var(--primary)' : '2px solid transparent',
        color: activeTab === tabName ? 'var(--primary)' : 'var(--text-secondary)',
        fontWeight: activeTab === tabName ? 'bold' as const : 'normal' as const,
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        marginBottom: '-2px'
    });

    return (
        <div>
            <h2 style={{ marginBottom: '2rem', textAlign: 'center' }}>Panel del Tutor</h2>

            {/* Tabs */}
            <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem', borderBottom: '2px solid var(--border-color)' }}>
                <button
                    onClick={() => setActiveTab('content')}
                    style={getTabStyle('content')}
                >
                    Contenido
                </button>
                <button
                    onClick={() => setActiveTab('metrics')}
                    style={getTabStyle('metrics')}
                >
                    Métricas y Dominio
                </button>
                <button
                    onClick={() => setActiveTab('recommendations')}
                    style={getTabStyle('recommendations')}
                >
                    Recomendaciones
                </button>
            </div>

            {/* Content */}
            {activeTab === 'content' && (
                <div style={{ display: 'grid', gap: '2rem' }}>
                    <section>
                        <UploadForm />
                    </section>
                    <section>
                        <UploadList />
                    </section>
                </div>
            )}

            {activeTab === 'metrics' && (
                <MetricsDashboard
                    studentId={STUDENT_ID}
                    subjectId={SUBJECT_ID}
                    termId={TERM_ID}
                />
            )}

            {activeTab === 'recommendations' && (
                <RecommendationList
                    studentId={STUDENT_ID}
                    subjectId={SUBJECT_ID}
                    termId={TERM_ID}
                    tutorId={TUTOR_ID}
                />
            )}
        </div>
    );
}
