"""Creates the schema and the sample customers. Runs every time the server starts; existing data is kept."""

import db

SCHEMA = """
CREATE SEQUENCE IF NOT EXISTS booking_ids START 1000;

CREATE TABLE IF NOT EXISTS customers (
  id text PRIMARY KEY, name text NOT NULL, phone text NOT NULL,
  company text NOT NULL, plan text NOT NULL, address text NOT NULL
);

CREATE TABLE IF NOT EXISTS stores (
  id text PRIMARY KEY, customer_id text NOT NULL REFERENCES customers(id),
  name text NOT NULL, address text NOT NULL
);
CREATE INDEX IF NOT EXISTS stores_customer_id ON stores(customer_id);

CREATE TABLE IF NOT EXISTS inspection_history (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  store_id text NOT NULL REFERENCES stores(id), type text NOT NULL,
  date text NOT NULL, result text NOT NULL, notes text,
  UNIQUE (store_id, date, type)
);

CREATE TABLE IF NOT EXISTS inspections (
  id text PRIMARY KEY, customer_id text NOT NULL REFERENCES customers(id),
  type text NOT NULL, date text NOT NULL, time_slot text NOT NULL,
  status text NOT NULL DEFAULT 'confirmed', notes text
);
CREATE UNIQUE INDEX IF NOT EXISTS confirmed_inspection_slot
  ON inspections(date, time_slot) WHERE status = 'confirmed';
"""

CUSTOMERS = [
    ("C001", "Maria Rodriguez", "555-0101", "Apex Manufacturing", "premium", "742 Industrial Blvd, Atlanta GA"),
    ("C002", "James Chen", "555-0102", "Harbor Logistics", "basic", "1200 Port Way, Savannah GA"),
    ("C003", "Sarah Thompson", "555-0103", "Pinnacle Office Group", "premium", "88 Peachtree St, Atlanta GA"),
    ("C004", "David Kim", "555-0104", "Coastal Dining LLC", "basic", "445 Beach Rd, Tybee Island GA"),
    ("C005", "Rachel Foster", "555-0105", "Summit Healthcare", "enterprise", "3200 Medical Center Dr, Augusta GA"),
]

HISTORY = [
    ("C001-0001", "fire", "2025-09-15", "pass", "Annual fire safety - all clear"),
    ("C002-0001", "fire", "2025-12-05", "fail", "Emergency exit blocked, citation issued"),
]


async def seed() -> None:
    async with db.pool.acquire() as conn:
        await conn.execute(SCHEMA)
        await conn.executemany(
            "INSERT INTO customers (id, name, phone, company, plan, address) VALUES ($1, $2, $3, $4, $5, $6)"
            " ON CONFLICT (id) DO NOTHING",
            CUSTOMERS,
        )
        # Each sample customer has one store, at their address.
        await conn.executemany(
            "INSERT INTO stores (id, customer_id, name, address) VALUES ($1, $2, $3, $4) ON CONFLICT (id) DO NOTHING",
            [(f"{c[0]}-0001", c[0], c[3], c[5]) for c in CUSTOMERS],
        )
        await conn.executemany(
            "INSERT INTO inspection_history (store_id, type, date, result, notes) VALUES ($1, $2, $3, $4, $5)"
            " ON CONFLICT (store_id, date, type) DO NOTHING",
            HISTORY,
        )
