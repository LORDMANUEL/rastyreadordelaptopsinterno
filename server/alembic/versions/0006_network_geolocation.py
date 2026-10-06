"""network geolocation fields

Revision ID: 0006_network_geolocation
Revises: 0005_device_auth_lifecycle
"""

from alembic import op
import sqlalchemy as sa

revision = "0006_network_geolocation"
down_revision = "0005_device_auth_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for name, column in (
        ("geo_country_code", sa.Column("geo_country_code", sa.String(length=8), nullable=True)),
        ("geo_country_name", sa.Column("geo_country_name", sa.String(length=120), nullable=True)),
        ("geo_region_name", sa.Column("geo_region_name", sa.String(length=160), nullable=True)),
        ("geo_city_name", sa.Column("geo_city_name", sa.String(length=160), nullable=True)),
        ("geo_accuracy_km", sa.Column("geo_accuracy_km", sa.Integer(), nullable=True)),
        ("geo_updated_at", sa.Column("geo_updated_at", sa.DateTime(timezone=True), nullable=True)),
    ):
        op.add_column("devices", column)

    for name, column in (
        ("geo_country_code", sa.Column("geo_country_code", sa.String(length=8), nullable=True)),
        ("geo_region_name", sa.Column("geo_region_name", sa.String(length=160), nullable=True)),
        ("geo_city_name", sa.Column("geo_city_name", sa.String(length=160), nullable=True)),
        ("geo_accuracy_km", sa.Column("geo_accuracy_km", sa.Integer(), nullable=True)),
    ):
        op.add_column("device_observations", column)


def downgrade() -> None:
    for name in (
        "geo_accuracy_km",
        "geo_city_name",
        "geo_region_name",
        "geo_country_code",
    ):
        op.drop_column("device_observations", name)

    for name in (
        "geo_updated_at",
        "geo_accuracy_km",
        "geo_city_name",
        "geo_region_name",
        "geo_country_name",
        "geo_country_code",
    ):
        op.drop_column("devices", name)
