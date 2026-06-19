from sqlalchemy import create_engine, MetaData, text
from main import app, db  # <- jouw Flask app + SQLAlchemy db
import json

SOURCE_DB = "sqlite:///website-copy.db"
TARGET_DB = "sqlite:///website.db"

source_engine = create_engine(SOURCE_DB)
target_engine = create_engine(TARGET_DB)

source_conn = source_engine.connect()
target_conn = target_engine.connect()

source_meta = MetaData()
target_meta = MetaData()

source_meta.reflect(bind=source_engine)
target_meta.reflect(bind=target_engine)

TABLE_ORDER = [
    "user",
    "waardes",
    "esp_device",
    "measurement",
    "couple_request",
    "device",
    'triggers'
]

SKIP_TABLES = ["triggers", "waardes"]


# ---------- STEP 1: CLEAR TARGET DB ----------
def clear_target():
    print("🧹 Clearing target DB...")

    target_conn.execute(text("PRAGMA foreign_keys = OFF"))

    for table in reversed(TABLE_ORDER):
        if table in target_meta.tables:
            target_conn.execute(
                text(f"DELETE FROM {table}")
            )

    target_conn.commit()


# ---------- STEP 2: COPY TABLE ----------
def copy_table(table_name):
    print(f"\n📦 Migrating {table_name}...")

    if table_name not in source_meta.tables:
        print(f"⚠️ Missing in source: {table_name}")
        return

    if table_name not in target_meta.tables:
        print(f"⚠️ Missing in target: {table_name}")
        return

    source_table = source_meta.tables[table_name]
    target_table = target_meta.tables[table_name]

    rows = source_conn.execute(source_table.select()).mappings().all()

    print(f"→ {len(rows)} rows")

    if not rows:
        return

    batch = []

    for row in rows:
        data = dict(row)

        # optional safety cleanup
        data = {k: v for k, v in data.items()}

        batch.append(data)

    target_conn.execute(target_table.insert(), batch)
    target_conn.commit()

    print(f"✅ {table_name} done")


# ---------- STEP 3: RUN MIGRATION ----------
def run():
    print("🚀 Starting migration...")

    clear_target()

    for table in TABLE_ORDER:
        if table in SKIP_TABLES:
            print(f"⏭ Skipping {table}")
            continue

        copy_table(table)

    print("\n🎉 Migration complete!")


if __name__ == "__main__":
    with app.app_context():  # belangrijk voor Flask-SQLAlchemy safety
        run()