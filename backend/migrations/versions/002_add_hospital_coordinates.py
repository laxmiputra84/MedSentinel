"""Add hospital latitude and longitude coordinates

Revision ID: 002_add_hospital_coordinates
Revises: 001_initial_schema
Create Date: 2026-10-01 22:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '002_add_hospital_coordinates'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    existing_columns = {col['name'] for col in inspector.get_columns('hospitals')}

    if 'latitude' not in existing_columns:
        op.add_column('hospitals', sa.Column('latitude', sa.Float(), nullable=True))
    if 'longitude' not in existing_columns:
        op.add_column('hospitals', sa.Column('longitude', sa.Float(), nullable=True))

def downgrade() -> None:
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    existing_columns = {col['name'] for col in inspector.get_columns('hospitals')}

    if 'longitude' in existing_columns:
        op.drop_column('hospitals', 'longitude')
    if 'latitude' in existing_columns:
        op.drop_column('hospitals', 'latitude')
