from pathlib import Path
from datetime import date
import hashlib
import hmac
import sqlite3

import pandas as pd


BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
DB = BASE / "ocean_freight.db"

TODAY = date.today()


# ---------- Password Management ----------

def hash_password(password, salt=None):
    salt = salt or __import__('os').urandom(16).hex()

    digest = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        salt.encode(),
        200_000
    ).hex()

    return f"{salt}${digest}"


def verify_password(password, stored):
    try:
        salt, digest = stored.split('$', 1)

        return hmac.compare_digest(
            hash_password(password, salt).split('$', 1)[1],
            digest
        )

    except Exception:
        return False


# ---------- Database Connection ----------

def connect():
    conn = sqlite3.connect(DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    return conn


# ---------- Database Initialization ----------

def init_db():
    with connect() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS users(
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS rates(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            carrier TEXT NOT NULL,
            origin_port TEXT NOT NULL,
            destination_port TEXT NOT NULL,
            container_type TEXT NOT NULL,
            rate_usd REAL NOT NULL,
            transit_days INTEGER NOT NULL,
            effective_from TEXT DEFAULT '',
            UNIQUE(
                carrier,
                origin_port,
                destination_port,
                container_type
            )
        );

        CREATE TABLE IF NOT EXISTS shipments(
            shipment_id TEXT PRIMARY KEY,
            carrier TEXT NOT NULL,
            origin_port TEXT NOT NULL,
            destination_port TEXT NOT NULL,
            container_type TEXT NOT NULL,
            departure_date TEXT NOT NULL,
            expected_arrival TEXT NOT NULL,
            delivered_date TEXT DEFAULT '',
            invoice_amount_usd REAL DEFAULT 0,
            status_override TEXT DEFAULT '',
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS email_logs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_subject TEXT,
            action TEXT,
            details TEXT,
            processed_at TEXT DEFAULT CURRENT_TIMESTAMP,
            email_hash TEXT UNIQUE
        );
        ''')

        # Seed demo users
        if c.execute(
            'SELECT COUNT(*) FROM users'
        ).fetchone()[0] == 0:

            c.execute(
                'INSERT INTO users VALUES(?,?,?)',
                ('admin', hash_password('Admin@123'), 'Admin')
            )

            c.execute(
                'INSERT INTO users VALUES(?,?,?)',
                ('user', hash_password('User@123'), 'User')
            )

        # Seed carrier rates
        if c.execute(
            'SELECT COUNT(*) FROM rates'
        ).fetchone()[0] == 0:

            df = pd.read_csv(
                DATA / 'carrier_rates.csv'
            ).fillna('')

            for _, r in df.iterrows():
                c.execute(
                    '''
                    INSERT OR IGNORE INTO rates(
                        carrier,
                        origin_port,
                        destination_port,
                        container_type,
                        rate_usd,
                        transit_days
                    )
                    VALUES(?,?,?,?,?,?)
                    ''',
                    (
                        r.carrier,
                        r.origin_port,
                        r.destination_port,
                        r.container_type,
                        float(r.rate_usd),
                        int(r.transit_days)
                    )
                )

        # Seed sample shipments
        if c.execute(
            'SELECT COUNT(*) FROM shipments'
        ).fetchone()[0] == 0:

            df = pd.read_csv(
                DATA / 'sample_shipments.csv'
            ).fillna('')

            for _, r in df.iterrows():
                c.execute(
                    '''
                    INSERT OR IGNORE INTO shipments(
                        shipment_id,
                        carrier,
                        origin_port,
                        destination_port,
                        container_type,
                        departure_date,
                        expected_arrival,
                        delivered_date,
                        invoice_amount_usd
                    )
                    VALUES(?,?,?,?,?,?,?,?,?)
                    ''',
                    (
                        r.shipment_id,
                        r.carrier,
                        r.origin_port,
                        r.destination_port,
                        r.container_type,
                        r.departure_date,
                        r.expected_arrival,
                        r.delivered_date,
                        float(r.invoice_amount_usd or 0)
                    )
                )


# ---------- Query Helpers ----------

def query(sql, params=()):
    with connect() as c:
        return pd.read_sql_query(sql, c, params=params)


def execute(sql, params=()):
    with connect() as c:
        c.execute(sql, params)


# ---------- Shipment Status ----------

def status_for(row):
    if row.get('delivered_date') and str(
        row.get('delivered_date')
    ).strip():
        return 'Delivered'

    if row.get('status_override') in ('Delayed', 'In Transit'):
        return row['status_override']

    try:
        return (
            'Delayed'
            if date.fromisoformat(
                str(row['expected_arrival'])
            ) < TODAY
            else 'In Transit'
        )

    except Exception:
        return 'In Transit'






    