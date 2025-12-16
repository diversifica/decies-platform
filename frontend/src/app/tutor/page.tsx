import UploadForm from '../../components/tutor/UploadForm';
import UploadList from '../../components/tutor/UploadList';

export default function TutorPage() {
    return (
        <div>
            <h2 style={{ marginBottom: '2rem', textAlign: 'center' }}>Panel del Tutor</h2>

            <div style={{ display: 'grid', gap: '2rem' }}>
                <section>
                    <UploadForm />
                </section>

                <section>
                    <UploadList />
                </section>
            </div>
        </div>
    );
}
