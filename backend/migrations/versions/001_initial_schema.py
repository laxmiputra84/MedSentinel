"""Initial MedSentinel schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-31 22:50:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(150), nullable=False, unique=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('blood_group', sa.String(20), nullable=True),
        sa.Column('allergies', sa.Text(), nullable=True),
        sa.Column('emergency_contact', sa.String(50), nullable=True),
        sa.Column('schemes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # Refresh tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token', sa.String(500), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('revoked', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # Hospitals table
    op.create_table(
        'hospitals',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('location', sa.String(200), nullable=True),
        sa.Column('specialization', sa.String(200), nullable=True),
        sa.Column('rating', sa.Float(), server_default='0.0'),
        sa.Column('distance', sa.Float(), server_default='0.0'),
        sa.Column('cost_range', sa.String(100), nullable=True),
        sa.Column('schemes', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(255), nullable=True),
        sa.Column('facilities', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('email', sa.String(100), nullable=True)
    )

    # Schemes table
    op.create_table(
        'schemes',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('name', sa.String(200), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('coverage', sa.String(100), nullable=True),
        sa.Column('eligibility', sa.Text(), nullable=True),
        sa.Column('type', sa.String(50), nullable=True)
    )

    # Saved Items table
    op.create_table(
        'saved_items',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('hospital_id', sa.Integer(), sa.ForeignKey('hospitals.id', ondelete='CASCADE'), nullable=False),
        sa.Column('saved_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('user_id', 'hospital_id', name='uix_user_hospital_saved')
    )

    # User Documents table
    op.create_table(
        'user_documents',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('doc_type', sa.String(100), server_default='Other', nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('original_name', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_type', sa.String(100), nullable=False),
        sa.Column('file_size', sa.Integer(), server_default='0'),
        sa.Column('upload_date', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('status', sa.String(50), server_default='active')
    )

    # Appointments table
    op.create_table(
        'appointments',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('email', sa.String(150), nullable=False),
        sa.Column('preferred_date', sa.String(50), nullable=False),
        sa.Column('preferred_time', sa.String(50), nullable=False),
        sa.Column('department', sa.String(100), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), server_default='confirmed'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # Insurances table
    op.create_table(
        'insurances',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('provider', sa.String(200), nullable=False),
        sa.Column('coverage_amount', sa.Float(), server_default='0.0'),
        sa.Column('premium_monthly', sa.Float(), server_default='0.0'),
        sa.Column('premium_annual', sa.Float(), server_default='0.0'),
        sa.Column('coverage_type', sa.String(100), nullable=True),
        sa.Column('inclusions', sa.Text(), nullable=True),
        sa.Column('exclusions', sa.Text(), nullable=True),
        sa.Column('eligibility_age_min', sa.Integer(), server_default='18'),
        sa.Column('eligibility_age_max', sa.Integer(), server_default='65'),
        sa.Column('waiting_period_days', sa.Integer(), server_default='30'),
        sa.Column('cashless_network', sa.Integer(), server_default='5000'),
        sa.Column('claim_settlement_days', sa.Integer(), server_default='30'),
        sa.Column('features', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(255), nullable=True),
        sa.Column('rating', sa.Float(), server_default='4.5'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # User Insurances table
    op.create_table(
        'user_insurances',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('insurance_id', sa.Integer(), sa.ForeignKey('insurances.id', ondelete='CASCADE'), nullable=False),
        sa.Column('policy_number', sa.String(100), nullable=False, unique=True),
        sa.Column('enrollment_date', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('status', sa.String(50), server_default='active'),
        sa.Column('coverage_start_date', sa.String(50), nullable=True),
        sa.Column('coverage_end_date', sa.String(50), nullable=True),
        sa.Column('sum_insured', sa.Float(), server_default='0.0'),
        sa.Column('dependents', sa.Text(), nullable=True)
    )

    # Insurance Claims table
    op.create_table(
        'insurance_claims',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('insurance_id', sa.Integer(), sa.ForeignKey('insurances.id', ondelete='SET NULL'), nullable=True),
        sa.Column('hospital_id', sa.Integer(), sa.ForeignKey('hospitals.id', ondelete='SET NULL'), nullable=True),
        sa.Column('claim_amount', sa.Float(), nullable=False),
        sa.Column('claim_date', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('claim_status', sa.String(50), server_default='pending'),
        sa.Column('claim_description', sa.Text(), nullable=True),
        sa.Column('documents', sa.Text(), nullable=True)
    )

    # OTP codes table
    op.create_table(
        'otp_codes',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('phone', sa.String(20), nullable=False, index=True),
        sa.Column('otp_code', sa.String(10), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('verified_until', sa.DateTime(), nullable=True),
        sa.Column('attempts', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'))
    )

def downgrade() -> None:
    op.drop_table('otp_codes')
    op.drop_table('insurance_claims')
    op.drop_table('user_insurances')
    op.drop_table('insurances')
    op.drop_table('appointments')
    op.drop_table('user_documents')
    op.drop_table('saved_items')
    op.drop_table('schemes')
    op.drop_table('hospitals')
    op.drop_table('refresh_tokens')
    op.drop_table('users')
