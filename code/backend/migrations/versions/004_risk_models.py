from typing import Any

from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None

RISK_TABLES = (
    "risk_assessments",
    "risk_metrics",
    "alert_rules",
    "risk_alerts",
    "risk_limits",
)


def _tables() -> list:
    import importlib

    importlib.import_module("models")
    from models.base import Base

    return [Base.metadata.tables[name] for name in RISK_TABLES]


def upgrade() -> Any:
    bind = op.get_bind()
    op.execute("DROP TABLE IF EXISTS risk_assessments CASCADE")
    op.execute("DROP TYPE IF EXISTS riskassessmenttype")
    for table in _tables():
        table.create(bind=bind, checkfirst=True)


def downgrade() -> Any:
    for name in reversed(RISK_TABLES):
        op.execute(f"DROP TABLE IF EXISTS {name} CASCADE")
    op.execute("DROP TYPE IF EXISTS risktype")
