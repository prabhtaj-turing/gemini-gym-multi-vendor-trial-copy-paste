from common_utils.print_log import print_log
"""
create_sample_dbs.py – build two realistic DuckDB databases
and synchronise SimulationEngine’s JSON snapshot *using only the global
db_manager*.

Databases created
-----------------
- main_db.duckdb      : customers & orders
- inventory_db.duckdb : products & stock_levels
"""

import os
import datetime
import random
import duckdb

# Make sure the APIs folder is on PYTHONPATH before running this script.
from mysql.SimulationEngine.db import db_manager

# ---------------------------------------------------------------------------
# Paths and housekeeping
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DB_DIR = os.path.join(BASE_DIR, "SampleDBs")
os.makedirs(SAMPLE_DB_DIR, exist_ok=True)

MAIN_DB = os.path.join(SAMPLE_DB_DIR, "main_db.duckdb")
INV_DB = os.path.join(SAMPLE_DB_DIR, "inventory_db.duckdb")

# Ensure idempotency: delete old DB files if present.
for fp in (MAIN_DB, INV_DB):
    if os.path.exists(fp):
        os.remove(fp)

# ---------------------------------------------------------------------------
# Helper for bulk inserts
# ---------------------------------------------------------------------------
def execmany(conn, sql, rows):
    conn.execute("BEGIN")
    conn.executemany(sql, rows)
    conn.execute("COMMIT")

# ---------------------------------------------------------------------------
# 1. Build main_db.duckdb
# ---------------------------------------------------------------------------
with duckdb.connect(MAIN_DB) as con:
    con.execute(
        """
        CREATE TABLE customers (
            id         INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name  TEXT,
            email      TEXT UNIQUE,
            city       TEXT
        );
        CREATE TABLE orders (
            id           INTEGER PRIMARY KEY,
            order_date   DATE,
            customer_id  INTEGER REFERENCES customers(id),
            total_amount DECIMAL(10,2)
        );
        """
    )

    first_names = ["Alice", "Bob", "Charlie", "Diana", "Eve",
                   "Frank", "Grace", "Hannah", "Ivan", "Julia"]
    last_names = ["Smith", "Johnson", "Brown", "Taylor", "Davis",
                  "Miller", "Wilson", "Moore", "Clark", "Hall"]
    cities = ["New York", "London", "Paris", "Berlin", "Tokyo"]

    customers = [
        (
            i + 1,
            first_names[i],
            last_names[i],
            f"{first_names[i].lower()}.{last_names[i].lower()}@example.com",
            random.choice(cities),
        )
        for i in range(10)
    ]
    execmany(con, "INSERT INTO customers VALUES (?, ?, ?, ?, ?)", customers)

    today = datetime.date.today()
    orders = []
    oid = 1
    for cust_id in range(1, 11):
        for _ in range(2):  # two orders per customer
            days_ago = random.randint(1, 365)
            orders.append(
                (
                    oid,
                    today - datetime.timedelta(days=days_ago),
                    cust_id,
                    round(random.uniform(20, 500), 2),
                )
            )
            oid += 1
    execmany(con, "INSERT INTO orders VALUES (?, ?, ?, ?)", orders)

# ---------------------------------------------------------------------------
# 2. Build inventory_db.duckdb
# ---------------------------------------------------------------------------
with duckdb.connect(INV_DB) as con:
    con.execute(
        """
        CREATE TABLE products (
            id          INTEGER PRIMARY KEY,
            sku         TEXT UNIQUE,
            name        TEXT,
            category    TEXT,
            unit_price  DECIMAL(10,2)
        );
        CREATE TABLE stock_levels (
            product_id  INTEGER REFERENCES products(id),
            warehouse   TEXT,
            quantity    INTEGER,
            PRIMARY KEY (product_id, warehouse)
        );
        """
    )

    items = [
        ("LED Monitor 24″", "Electronics"),
        ("Mechanical Keyboard", "Electronics"),
        ("USB-C Hub 7-port", "Electronics"),
        ("Office Chair Ergo", "Furniture"),
        ("Standing Desk 120 cm", "Furniture"),
        ("Notebook A5 Dot-grid", "Stationery"),
        ("Gel Pen 0.5 mm", "Stationery"),
        ("Wireless Mouse", "Electronics"),
    ]
    products = [
        (i + 1, f"SKU{i+1001}", name, cat, round(random.uniform(5, 300), 2))
        for i, (name, cat) in enumerate(items)
    ]
    execmany(con, "INSERT INTO products VALUES (?, ?, ?, ?, ?)", products)

    warehouses = ["WHS-NY", "WHS-EU"]
    stocks = [
        (pid, wh, random.randint(0, 150))
        for pid in range(1, 9)
        for wh in warehouses
    ]
    execmany(con, "INSERT INTO stock_levels VALUES (?, ?, ?)", stocks)

# ---------------------------------------------------------------------------
# 3. Tell the existing db_manager about inventory_db and persist state
# ---------------------------------------------------------------------------
inventory_path_rel = os.path.relpath(INV_DB, start=db_manager._database_directory)
# Use absolute path in ATTACH to avoid path ambiguity.
db_manager.execute_query(f"ATTACH DATABASE '{INV_DB}' AS inventory_db")

# Persist the snapshot (includes main_db and inventory_db) and close.
db_manager.close_main_connection()

print_log("Databases & snapshot created and synced")
print_log(f"   - {MAIN_DB}")
print_log(f"   - {INV_DB}")
print_log(f"   - Snapshot: {db_manager._state_path}")