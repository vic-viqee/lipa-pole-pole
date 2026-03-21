from sqlalchemy import inspect, text

from app.db.base import Base
from app.db.session import engine


def ensure_database_schema() -> None:
    Base.metadata.create_all(bind=engine)

    with engine.begin() as conn:
        inspector = inspect(conn)
        if "installment_plans" not in inspector.get_table_names():
            return

        cols = {col["name"] for col in inspector.get_columns("installment_plans")}
        if "tracking_token" in cols:
            return

        dialect = conn.dialect.name
        if dialect == "postgresql":
            conn.execute(text("ALTER TABLE installment_plans ADD COLUMN tracking_token VARCHAR"))
            conn.execute(
                text(
                    "UPDATE installment_plans "
                    "SET tracking_token = md5(random()::text || clock_timestamp()::text) "
                    "WHERE tracking_token IS NULL"
                )
            )
            conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ix_installment_plans_tracking_token "
                    "ON installment_plans (tracking_token)"
                )
            )
        elif dialect == "sqlite":
            conn.execute(text("ALTER TABLE installment_plans ADD COLUMN tracking_token TEXT"))
            conn.execute(
                text(
                    "UPDATE installment_plans "
                    "SET tracking_token = lower(hex(randomblob(16))) "
                    "WHERE tracking_token IS NULL"
                )
            )
