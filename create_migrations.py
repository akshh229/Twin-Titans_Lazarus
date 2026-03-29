"""
LAZARUS - Database Migration Creator
=====================================
Creates all Alembic migration files for the Lazarus project
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent

# First, create all necessary directories
DIRECTORIES = [
    "backend",
    "backend/migrations",
    "backend/migrations/versions",
]

print("Creating directory structure...")
for dir_path in DIRECTORIES:
    full_path = BASE_DIR / dir_path
    full_path.mkdir(parents=True, exist_ok=True)
    print(f"  ✓ {dir_path}")
print()

def create_file(path: str, content: str) -> bool:
    """Create file with content, creating parent dirs if needed"""
    try:
        full_path = BASE_DIR / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content.lstrip())
        print(f"  ✓ Created: {path}")
        return True
    except Exception as e:
        print(f"  ✗ ERROR creating {path}: {e}")
        return False

print("=" * 80)
print(" LAZARUS - Creating Database Migrations")
print("=" * 80)
print()

# ============================================================================
# 1. backend/alembic.ini
# ============================================================================

ALEMBIC_INI = """
[alembic]
script_location = migrations
prepend_sys_path = .
version_path_separator = os

sqlalchemy.url = postgresql://lazarus_user:lazarus_password_change_me@localhost:5432/lazarus

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""

create_file("backend/alembic.ini", ALEMBIC_INI)

# ============================================================================
# 2. backend/migrations/env.py
# ============================================================================

MIGRATIONS_ENV = """
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from app.database import Base
from app.models import *  # Import all models

config = context.config
fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
"""

create_file("backend/migrations/env.py", MIGRATIONS_ENV)

# ============================================================================
# 3. backend/migrations/script.py.mako
# ============================================================================

SCRIPT_MAKO = '''
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade():
    ${upgrades if upgrades else "pass"}


def downgrade():
    ${downgrades if downgrades else "pass"}
'''

create_file("backend/migrations/script.py.mako", SCRIPT_MAKO)

# ============================================================================
# 4. backend/migrations/versions/001_initial_tables.py
# ============================================================================

INITIAL_MIGRATION = """
\"\"\"Initial tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

\"\"\"
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ============================================================================
    # STAGING TABLES - Raw ingested data
    # ============================================================================
    
    # stg_patient_demographics
    op.create_table('stg_patient_demographics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_raw_id', sa.String(length=50), nullable=False),
        sa.Column('name_cipher', sa.Text(), nullable=True),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('ward_code', sa.String(length=10), nullable=True),
        sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stg_patient_demographics_id'), 'stg_patient_demographics', ['id'], unique=False)
    op.create_index(op.f('ix_stg_patient_demographics_patient_raw_id'), 'stg_patient_demographics', ['patient_raw_id'], unique=False)
    
    # stg_telemetry_logs
    op.create_table('stg_telemetry_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_raw_id', sa.String(length=50), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('hex_payload', sa.Text(), nullable=False),
        sa.Column('source_device', sa.String(length=50), nullable=True),
        sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stg_telemetry_logs_id'), 'stg_telemetry_logs', ['id'], unique=False)
    op.create_index(op.f('ix_stg_telemetry_logs_patient_raw_id'), 'stg_telemetry_logs', ['patient_raw_id'], unique=False)
    op.create_index(op.f('ix_stg_telemetry_logs_timestamp'), 'stg_telemetry_logs', ['timestamp'], unique=False)
    
    # stg_prescription_audit
    op.create_table('stg_prescription_audit',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_raw_id', sa.String(length=50), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('age', sa.Integer(), nullable=False),
        sa.Column('med_cipher_text', sa.String(length=255), nullable=False),
        sa.Column('dosage', sa.String(length=100), nullable=True),
        sa.Column('route', sa.String(length=50), nullable=True),
        sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stg_prescription_audit_id'), 'stg_prescription_audit', ['id'], unique=False)
    op.create_index(op.f('ix_stg_prescription_audit_patient_raw_id'), 'stg_prescription_audit', ['patient_raw_id'], unique=False)
    
    # ============================================================================
    # CLEANED TABLES - Decoded and validated data
    # ============================================================================
    
    # clean_telemetry
    op.create_table('clean_telemetry',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_raw_id', sa.String(length=50), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('hex_payload', sa.Text(), nullable=True),
        sa.Column('bpm', sa.Integer(), nullable=True),
        sa.Column('oxygen', sa.Integer(), nullable=True),
        sa.Column('parity_flag', sa.String(length=4), nullable=True),
        sa.Column('quality_flag', sa.String(length=10), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.CheckConstraint("parity_flag IN ('even', 'odd')", name=op.f('ck_clean_telemetry_parity_flag')),
        sa.CheckConstraint("quality_flag IN ('good', 'bad', 'missing')", name=op.f('ck_clean_telemetry_quality_flag')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('patient_raw_id', 'timestamp', name=op.f('uq_clean_telemetry_patient_timestamp'))
    )
    op.create_index(op.f('ix_clean_telemetry_id'), 'clean_telemetry', ['id'], unique=False)
    op.create_index(op.f('ix_clean_telemetry_patient_raw_id'), 'clean_telemetry', ['patient_raw_id'], unique=False)
    op.create_index(op.f('ix_clean_telemetry_timestamp'), 'clean_telemetry', ['timestamp'], unique=False)
    
    # clean_prescriptions
    op.create_table('clean_prescriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_raw_id', sa.String(length=50), nullable=False),
        sa.Column('age', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('med_cipher_text', sa.String(length=255), nullable=False),
        sa.Column('med_decoded_name', sa.String(length=255), nullable=True),
        sa.Column('dosage', sa.String(length=100), nullable=True),
        sa.Column('route', sa.String(length=50), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_clean_prescriptions_id'), 'clean_prescriptions', ['id'], unique=False)
    op.create_index(op.f('ix_clean_prescriptions_patient_raw_id'), 'clean_prescriptions', ['patient_raw_id'], unique=False)
    
    # clean_demographics
    op.create_table('clean_demographics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_raw_id', sa.String(length=50), nullable=False),
        sa.Column('name_cipher', sa.Text(), nullable=True),
        sa.Column('decoded_name', sa.String(length=255), nullable=True),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('ward', sa.String(length=50), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_clean_demographics_id'), 'clean_demographics', ['id'], unique=False)
    op.create_index(op.f('ix_clean_demographics_patient_raw_id'), 'clean_demographics', ['patient_raw_id'], unique=False)
    
    # ============================================================================
    # IDENTITY RECONCILIATION TABLES
    # ============================================================================
    
    # patient_alias
    op.create_table('patient_alias',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_raw_id', sa.String(length=50), nullable=False),
        sa.Column('parity_flag', sa.String(length=4), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('sample_count', sa.Integer(), nullable=True),
        sa.Column('confidence_score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.CheckConstraint("parity_flag IN ('even', 'odd')", name=op.f('ck_patient_alias_parity_flag')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('patient_raw_id', 'parity_flag', name=op.f('uq_patient_alias_raw_id_parity'))
    )
    op.create_index(op.f('ix_patient_alias_id'), 'patient_alias', ['id'], unique=False)
    op.create_index(op.f('ix_patient_alias_patient_id'), 'patient_alias', ['patient_id'], unique=True)
    
    # identity_audit_log
    op.create_table('identity_audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_raw_id', sa.String(length=50), nullable=True),
        sa.Column('parity_flag', sa.String(length=4), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=True),
        sa.Column('bpm_samples_used', sa.Integer(), nullable=True),
        sa.Column('decision_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_identity_audit_log_id'), 'identity_audit_log', ['id'], unique=False)
    op.create_index(op.f('ix_identity_audit_log_patient_id'), 'identity_audit_log', ['patient_id'], unique=False)
    
    # ============================================================================
    # ALERTS TABLE
    # ============================================================================
    
    # patient_alerts
    op.create_table('patient_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('alert_type', sa.String(length=50), nullable=True),
        sa.Column('opened_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('last_bpm', sa.Integer(), nullable=True),
        sa.Column('last_oxygen', sa.Integer(), nullable=True),
        sa.Column('consecutive_abnormal_count', sa.Integer(), nullable=True),
        sa.Column('consecutive_normal_count', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.CheckConstraint("status IN ('open', 'closed', 'acknowledged')", name=op.f('ck_patient_alerts_status')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_patient_alerts_id'), 'patient_alerts', ['id'], unique=False)
    op.create_index(op.f('ix_patient_alerts_patient_id'), 'patient_alerts', ['patient_id'], unique=False)
    op.create_index('ix_patient_alerts_open_status', 'patient_alerts', ['patient_id', 'status'], 
                    unique=False, postgresql_where=sa.text("status='open'"))


def downgrade():
    # Drop all tables in reverse order
    op.drop_index('ix_patient_alerts_open_status', table_name='patient_alerts')
    op.drop_index(op.f('ix_patient_alerts_patient_id'), table_name='patient_alerts')
    op.drop_index(op.f('ix_patient_alerts_id'), table_name='patient_alerts')
    op.drop_table('patient_alerts')
    
    op.drop_index(op.f('ix_identity_audit_log_patient_id'), table_name='identity_audit_log')
    op.drop_index(op.f('ix_identity_audit_log_id'), table_name='identity_audit_log')
    op.drop_table('identity_audit_log')
    
    op.drop_index(op.f('ix_patient_alias_patient_id'), table_name='patient_alias')
    op.drop_index(op.f('ix_patient_alias_id'), table_name='patient_alias')
    op.drop_table('patient_alias')
    
    op.drop_index(op.f('ix_clean_demographics_patient_raw_id'), table_name='clean_demographics')
    op.drop_index(op.f('ix_clean_demographics_id'), table_name='clean_demographics')
    op.drop_table('clean_demographics')
    
    op.drop_index(op.f('ix_clean_prescriptions_patient_raw_id'), table_name='clean_prescriptions')
    op.drop_index(op.f('ix_clean_prescriptions_id'), table_name='clean_prescriptions')
    op.drop_table('clean_prescriptions')
    
    op.drop_index(op.f('ix_clean_telemetry_timestamp'), table_name='clean_telemetry')
    op.drop_index(op.f('ix_clean_telemetry_patient_raw_id'), table_name='clean_telemetry')
    op.drop_index(op.f('ix_clean_telemetry_id'), table_name='clean_telemetry')
    op.drop_table('clean_telemetry')
    
    op.drop_index(op.f('ix_stg_prescription_audit_patient_raw_id'), table_name='stg_prescription_audit')
    op.drop_index(op.f('ix_stg_prescription_audit_id'), table_name='stg_prescription_audit')
    op.drop_table('stg_prescription_audit')
    
    op.drop_index(op.f('ix_stg_telemetry_logs_timestamp'), table_name='stg_telemetry_logs')
    op.drop_index(op.f('ix_stg_telemetry_logs_patient_raw_id'), table_name='stg_telemetry_logs')
    op.drop_index(op.f('ix_stg_telemetry_logs_id'), table_name='stg_telemetry_logs')
    op.drop_table('stg_telemetry_logs')
    
    op.drop_index(op.f('ix_stg_patient_demographics_patient_raw_id'), table_name='stg_patient_demographics')
    op.drop_index(op.f('ix_stg_patient_demographics_id'), table_name='stg_patient_demographics')
    op.drop_table('stg_patient_demographics')
"""

create_file("backend/migrations/versions/001_initial_tables.py", INITIAL_MIGRATION)

# ============================================================================
# 5. backend/migrations/versions/002_create_patient_view.py
# ============================================================================

PATIENT_VIEW_MIGRATION = """
\"\"\"Create patient view

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:01.000000

\"\"\"
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(\"\"\"
        CREATE MATERIALIZED VIEW patient_view AS
        SELECT 
            pa.patient_id,
            pa.patient_raw_id,
            pa.parity_flag,
            cd.decoded_name,
            cd.age,
            cd.ward,
            latest_vitals.bpm AS last_bpm,
            latest_vitals.oxygen AS last_oxygen,
            latest_vitals.timestamp AS last_vitals_timestamp,
            latest_vitals.quality_flag,
            COUNT(DISTINCT cp.id) AS prescription_count,
            EXISTS(
                SELECT 1 FROM patient_alerts 
                WHERE patient_alerts.patient_id = pa.patient_id 
                AND status = 'open'
            ) AS has_active_alert
        FROM patient_alias pa
        LEFT JOIN clean_demographics cd ON cd.patient_raw_id = pa.patient_raw_id
        LEFT JOIN LATERAL (
            SELECT bpm, oxygen, timestamp, quality_flag
            FROM clean_telemetry ct
            WHERE ct.patient_raw_id = pa.patient_raw_id
                AND ct.parity_flag = pa.parity_flag
                AND ct.quality_flag = 'good'
            ORDER BY timestamp DESC
            LIMIT 1
        ) latest_vitals ON true
        LEFT JOIN clean_prescriptions cp ON cp.patient_raw_id = pa.patient_raw_id
        GROUP BY pa.patient_id, pa.patient_raw_id, pa.parity_flag, 
                cd.decoded_name, cd.age, cd.ward,
                latest_vitals.bpm, latest_vitals.oxygen, 
                latest_vitals.timestamp, latest_vitals.quality_flag;

        CREATE UNIQUE INDEX idx_patient_view_id ON patient_view(patient_id);
    \"\"\")


def downgrade():
    op.execute("DROP MATERIALIZED VIEW IF EXISTS patient_view")
"""

create_file("backend/migrations/versions/002_create_patient_view.py", PATIENT_VIEW_MIGRATION)

# ============================================================================
# Summary
# ============================================================================

print()
print("=" * 80)
print(" ✅ MIGRATION FILES CREATED SUCCESSFULLY")
print("=" * 80)
print()
print("Files created:")
print("  1. backend/alembic.ini - Alembic configuration")
print("  2. backend/migrations/env.py - Migration environment setup")
print("  3. backend/migrations/script.py.mako - Migration template")
print("  4. backend/migrations/versions/001_initial_tables.py - All database tables")
print("  5. backend/migrations/versions/002_create_patient_view.py - Materialized view")
print()
print("Database tables included:")
print("  Staging Layer:")
print("    - stg_patient_demographics")
print("    - stg_telemetry_logs")
print("    - stg_prescription_audit")
print("  Cleaned Layer:")
print("    - clean_telemetry")
print("    - clean_prescriptions")
print("    - clean_demographics")
print("  Identity Layer:")
print("    - patient_alias")
print("    - identity_audit_log")
print("  Alerts Layer:")
print("    - patient_alerts")
print("  Views:")
print("    - patient_view (materialized)")
print()
print("Next steps:")
print("  1. Ensure PostgreSQL is running")
print("  2. Create database: createdb lazarus")
print("  3. Run migrations: cd backend && alembic upgrade head")
print()
print("=" * 80)
