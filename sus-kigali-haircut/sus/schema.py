"""Lightweight in-place schema upgrades — no Alembic dependency.

``db.create_all()`` only creates *missing tables*; it never adds a column to a
table that already exists. This module adds the columns the app gained after
the first release so an existing SQLite file (or an already-provisioned
Postgres database) keeps working after an update instead of throwing
"no such column".
"""
from sqlalchemy import inspect, text

from .models import db

# table name -> {column name: SQL type added to ALTER TABLE}
ADDED_COLUMNS = {
    "services": {
        "commission_rate": "FLOAT",
    },
    "transaction_items": {
        "commission_rate": "FLOAT",
        "commission_amount": "INTEGER DEFAULT 0",
    },
}


def ensure_schema():
    """Add any column this version needs that the live database lacks.

    Safe to run on every start: existing columns are left untouched and any
    missing ones are appended with their default, so no data is lost.
    """
    inspector = inspect(db.engine)
    tables = set(inspector.get_table_names())
    changed = []
    for table, columns in ADDED_COLUMNS.items():
        if table not in tables:
            continue  # create_all() will build it correctly anyway
        present = {c["name"] for c in inspector.get_columns(table)}
        for column, ddl in columns.items():
            if column in present:
                continue
            db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
            changed.append(f"{table}.{column}")
    if changed:
        db.session.commit()
    return changed
