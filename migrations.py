def create_schema_version_table(connection):
    connection.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER NOT NULL
        )
    """)

    connection.execute("""
        INSERT INTO schema_version (version)
        SELECT 0
        WHERE NOT EXISTS (
            SELECT 1 FROM schema_version
        )
    """)

    connection.commit()


def get_schema_version(connection):
    cursor = connection.execute("""
        SELECT version
        FROM schema_version
        LIMIT 1
    """)

    row = cursor.fetchone()

    return row[0]


def set_schema_version(version, connection):
    connection.execute("""
        UPDATE schema_version
        SET version = ?
    """, (version,))

    connection.commit()

def migrate_to_version_1(connection):
    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            amount REAL,
            category TEXT,
            description TEXT,
            transaction_type TEXT NOT NULL DEFAULT 'expense',
            transaction_date TEXT NOT NULL DEFAULT '1970-01-01',
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor = connection.execute("""
        PRAGMA table_info(transactions)
    """)

    columns = {
        row[1]
        for row in cursor.fetchall()
    }

    if "transaction_type" not in columns:
        connection.execute("""
            ALTER TABLE transactions
            ADD COLUMN transaction_type TEXT NOT NULL DEFAULT 'expense'
        """)

    if "transaction_date" not in columns:
        connection.execute("""
            ALTER TABLE transactions
            ADD COLUMN transaction_date TEXT NOT NULL DEFAULT '1970-01-01'
        """)

    connection.commit()

CURRENT_SCHEMA_VERSION = 1


def run_migrations(connection):
    create_schema_version_table(connection)

    current_version = get_schema_version(connection)

    if current_version < 1:
        migrate_to_version_1(connection)
        set_schema_version(1, connection)