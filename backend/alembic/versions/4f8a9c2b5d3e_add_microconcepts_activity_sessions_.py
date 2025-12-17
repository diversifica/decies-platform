"""add microconcepts, activity sessions, learning events, metrics, and mastery states

Revision ID: 4f8a9c2b5d3e
Revises: 31ad4590449b
Create Date: 2025-12-17 17:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4f8a9c2b5d3e'
down_revision: Union[str, None] = '31ad4590449b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create mastery_status enum
    try:
        op.execute("CREATE TYPE mastery_status AS ENUM ('dominant','in_progress','at_risk')")
    except Exception:
        # Enum already exists, continue
        pass



    # Create microconcepts table
    op.create_table(
        'microconcepts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subject_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('term_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('code', sa.String(length=50), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id', name='microconcepts_pkey'),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], name='microconcepts_subject_id_fkey'),
        sa.ForeignKeyConstraint(['term_id'], ['terms.id'], name='microconcepts_term_id_fkey'),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], name='microconcepts_topic_id_fkey'),
    )
    op.create_index('idx_microconcepts_subject', 'microconcepts', ['subject_id'])

    # Create microconcept_prerequisites table
    op.create_table(
        'microconcept_prerequisites',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('microconcept_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('prerequisite_microconcept_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id', name='microconcept_prerequisites_pkey'),
        sa.ForeignKeyConstraint(['microconcept_id'], ['microconcepts.id'], name='mc_prereq_microconcept_id_fkey'),
        sa.ForeignKeyConstraint(['prerequisite_microconcept_id'], ['microconcepts.id'], name='mc_prereq_prerequisite_id_fkey'),
    )

    # Create activity_types table
    op.create_table(
        'activity_types',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id', name='activity_types_pkey'),
        sa.UniqueConstraint('code', name='activity_types_code_key'),
    )

    # Create activity_sessions table
    op.create_table(
        'activity_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('activity_type_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subject_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('term_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='in_progress'),
        sa.Column('device_type', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id', name='activity_sessions_pkey'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], name='activity_sessions_student_id_fkey'),
        sa.ForeignKeyConstraint(['activity_type_id'], ['activity_types.id'], name='activity_sessions_activity_type_id_fkey'),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], name='activity_sessions_subject_id_fkey'),
        sa.ForeignKeyConstraint(['term_id'], ['terms.id'], name='activity_sessions_term_id_fkey'),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], name='activity_sessions_topic_id_fkey'),
    )
    op.create_index('idx_activity_sessions_student', 'activity_sessions', ['student_id'])

    # Create activity_session_items table
    op.create_table(
        'activity_session_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('presented_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id', name='activity_session_items_pkey'),
        sa.ForeignKeyConstraint(['session_id'], ['activity_sessions.id'], name='activity_session_items_session_id_fkey'),
        sa.ForeignKeyConstraint(['item_id'], ['items.id'], name='activity_session_items_item_id_fkey'),
    )

    # Create learning_events table
    op.create_table(
        'learning_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subject_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('term_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('microconcept_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('activity_type_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp_start', sa.DateTime(), nullable=False),
        sa.Column('timestamp_end', sa.DateTime(), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=False),
        sa.Column('attempt_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('response_normalized', sa.String(length=500), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column('hint_used', sa.String(length=50), nullable=True),
        sa.Column('difficulty_at_time', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id', name='learning_events_pkey'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], name='learning_events_student_id_fkey'),
        sa.ForeignKeyConstraint(['session_id'], ['activity_sessions.id'], name='learning_events_session_id_fkey'),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], name='learning_events_subject_id_fkey'),
        sa.ForeignKeyConstraint(['term_id'], ['terms.id'], name='learning_events_term_id_fkey'),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], name='learning_events_topic_id_fkey'),
        sa.ForeignKeyConstraint(['microconcept_id'], ['microconcepts.id'], name='learning_events_microconcept_id_fkey'),
        sa.ForeignKeyConstraint(['activity_type_id'], ['activity_types.id'], name='learning_events_activity_type_id_fkey'),
        sa.ForeignKeyConstraint(['item_id'], ['items.id'], name='learning_events_item_id_fkey'),
    )
    op.create_index('idx_learning_events_student', 'learning_events', ['student_id'])
    op.create_index('idx_learning_events_session', 'learning_events', ['session_id'])

    # Create metric_aggregates table
    op.create_table(
        'metric_aggregates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scope_type', sa.String(length=50), nullable=False),
        sa.Column('scope_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('window_start', sa.DateTime(), nullable=False),
        sa.Column('window_end', sa.DateTime(), nullable=False),
        sa.Column('accuracy', sa.Numeric(precision=6, scale=4), nullable=True),
        sa.Column('first_attempt_accuracy', sa.Numeric(precision=6, scale=4), nullable=True),
        sa.Column('error_rate', sa.Numeric(precision=6, scale=4), nullable=True),
        sa.Column('median_response_time_ms', sa.Integer(), nullable=True),
        sa.Column('attempts_per_item_avg', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('hint_rate', sa.Numeric(precision=6, scale=4), nullable=True),
        sa.Column('abandon_rate', sa.Numeric(precision=6, scale=4), nullable=True),
        sa.Column('computed_at', sa.DateTime(), nullable=False),
        sa.Column('metrics_version', sa.String(length=20), nullable=False, server_default='V1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id', name='metric_aggregates_pkey'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], name='metric_aggregates_student_id_fkey'),
    )
    op.create_index('idx_metric_aggregates_student', 'metric_aggregates', ['student_id'])

    # Create mastery_states table
    op.create_table(
        'mastery_states',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('microconcept_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mastery_score', sa.Numeric(precision=6, scale=4), nullable=False, server_default='0'),
        sa.Column('status', postgresql.ENUM('dominant', 'in_progress', 'at_risk', name='mastery_status', create_type=False), nullable=False, server_default='in_progress'),
        sa.Column('last_practice_at', sa.DateTime(), nullable=True),
        sa.Column('recommended_next_review_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('metrics_version', sa.String(length=20), nullable=False, server_default='V1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id', name='mastery_states_pkey'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], name='mastery_states_student_id_fkey'),
        sa.ForeignKeyConstraint(['microconcept_id'], ['microconcepts.id'], name='mastery_states_microconcept_id_fkey'),
    )
    op.create_index('idx_mastery_states_student', 'mastery_states', ['student_id'])

    # Add microconcept_id to items table (optional field)
    op.add_column('items', sa.Column('microconcept_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('items_microconcept_id_fkey', 'items', 'microconcepts', ['microconcept_id'], ['id'])


def downgrade() -> None:
    # Drop foreign key and column from items
    op.drop_constraint('items_microconcept_id_fkey', 'items', type_='foreignkey')
    op.drop_column('items', 'microconcept_id')

    # Drop tables in reverse order
    op.drop_index('idx_mastery_states_student', table_name='mastery_states')
    op.drop_table('mastery_states')

    op.drop_index('idx_metric_aggregates_student', table_name='metric_aggregates')
    op.drop_table('metric_aggregates')

    op.drop_index('idx_learning_events_session', table_name='learning_events')
    op.drop_index('idx_learning_events_student', table_name='learning_events')
    op.drop_table('learning_events')

    op.drop_table('activity_session_items')

    op.drop_index('idx_activity_sessions_student', table_name='activity_sessions')
    op.drop_table('activity_sessions')

    op.drop_table('activity_types')

    op.drop_table('microconcept_prerequisites')

    op.drop_index('idx_microconcepts_subject', table_name='microconcepts')
    op.drop_table('microconcepts')

    # Drop enum
    op.execute("DROP TYPE mastery_status")
