"""SQLite database setup and operations for the inventory application."""

from __future__ import annotations

import hashlib
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, Iterable, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "inventory.db"

DEFAULT_USERNAME = "Ruben jung shahi"
DEFAULT_PASSWORD = "Ruben123"


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT UNIQUE,
                name TEXT NOT NULL,
                description TEXT,
                unit_price REAL NOT NULL DEFAULT 0,
                quantity INTEGER NOT NULL DEFAULT 0,
                category TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL DEFAULT 0,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_number TEXT UNIQUE NOT NULL,
                customer_name TEXT,
                total REAL NOT NULL,
                sale_date TEXT NOT NULL,
                user_id INTEGER,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                item_type TEXT NOT NULL,
                item_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                line_total REAL NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_number TEXT UNIQUE NOT NULL,
                supplier_name TEXT,
                total REAL NOT NULL,
                purchase_date TEXT NOT NULL,
                user_id INTEGER,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS purchase_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_cost REAL NOT NULL,
                line_total REAL NOT NULL,
                FOREIGN KEY (purchase_id) REFERENCES purchases(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id)
            );

            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                user_id INTEGER,
                username TEXT,
                action TEXT NOT NULL,
                detail TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_sale_items_sale ON sale_items(sale_id);
            CREATE INDEX IF NOT EXISTS idx_purchase_items_purchase ON purchase_items(purchase_id);
            """
        )

    _ensure_default_user()


def _ensure_default_user() -> None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM users WHERE username = ?", (DEFAULT_USERNAME,)
        ).fetchone()
        if row is None:
            conn.execute(
                """
                INSERT INTO users (username, password_hash, full_name)
                VALUES (?, ?, ?)
                """,
                (DEFAULT_USERNAME, _hash_password(DEFAULT_PASSWORD), DEFAULT_USERNAME),
            )


def verify_login(username: str, password: str) -> Optional[dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, username, full_name FROM users WHERE username = ? AND password_hash = ?",
            (username.strip(), _hash_password(password)),
        ).fetchone()
        if row is None:
            return None
        return {"id": row["id"], "username": row["username"], "full_name": row["full_name"]}


def log_action(
    user_id: Optional[int], username: Optional[str], action: str, detail: str = ""
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO activity_log (ts, user_id, username, action, detail)
            VALUES (?, ?, ?, ?, ?)
            """,
            (_now(), user_id, username, action, detail),
        )


def _next_doc_number(conn: sqlite3.Connection, prefix: str, table: str, col: str) -> str:
    today = datetime.now().strftime("%Y%m%d")
    pattern = f"{prefix}-{today}-%"
    row = conn.execute(
        f"SELECT {col} FROM {table} WHERE {col} LIKE ? ORDER BY {col} DESC LIMIT 1",
        (pattern,),
    ).fetchone()
    if row is None:
        return f"{prefix}-{today}-001"
    last = row[0]
    try:
        n = int(last.split("-")[-1]) + 1
    except (ValueError, IndexError):
        n = 1
    return f"{prefix}-{today}-{n:03d}"


# --- Products ---


def list_products() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return list(
            conn.execute(
                "SELECT * FROM products ORDER BY name COLLATE NOCASE"
            ).fetchall()
        )


def add_product(
    sku: str,
    name: str,
    description: str,
    unit_price: float,
    quantity: int,
    category: str,
) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO products (sku, name, description, unit_price, quantity, category, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (sku or None, name, description, unit_price, quantity, category, _now()),
        )
        return int(cur.lastrowid)


def update_product(
    pid: int,
    sku: str,
    name: str,
    description: str,
    unit_price: float,
    quantity: int,
    category: str,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE products SET sku=?, name=?, description=?, unit_price=?, quantity=?, category=?
            WHERE id=?
            """,
            (sku or None, name, description, unit_price, quantity, category, pid),
        )


def delete_product(pid: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM products WHERE id=?", (pid,))


def get_product(pid: int) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()


def adjust_product_quantity(pid: int, delta: int, user_id: int, username: str) -> None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT quantity, name FROM products WHERE id=?", (pid,)
        ).fetchone()
        if row is None:
            raise ValueError("Product not found")
        new_qty = row["quantity"] + delta
        if new_qty < 0:
            raise ValueError("Quantity cannot be negative")
        conn.execute(
            "UPDATE products SET quantity=? WHERE id=?", (new_qty, pid)
        )
    log_action(
        user_id,
        username,
        "Stock update",
        f"Product #{pid} ({row['name']}): {delta:+d} → qty {new_qty}",
    )


def set_product_quantity(pid: int, new_qty: int, user_id: int, username: str) -> None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT quantity, name FROM products WHERE id=?", (pid,)
        ).fetchone()
        if row is None:
            raise ValueError("Product not found")
        if new_qty < 0:
            raise ValueError("Quantity cannot be negative")
        old = row["quantity"]
        conn.execute("UPDATE products SET quantity=? WHERE id=?", (new_qty, pid))
    log_action(
        user_id,
        username,
        "Stock set",
        f"Product #{pid} ({row['name']}): {old} → {new_qty}",
    )


# --- Services ---


def list_services() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return list(
            conn.execute("SELECT * FROM services ORDER BY name COLLATE NOCASE").fetchall()
        )


def add_service(code: str, name: str, description: str, price: float) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO services (code, name, description, price, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (code or None, name, description, price, _now()),
        )
        return int(cur.lastrowid)


def update_service(sid: int, code: str, name: str, description: str, price: float) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE services SET code=?, name=?, description=?, price=? WHERE id=?
            """,
            (code or None, name, description, price, sid),
        )


def delete_service(sid: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM services WHERE id=?", (sid,))


# --- Sales ---


def create_sale(
    customer_name: str,
    notes: str,
    lines: Iterable[tuple[str, int, int, float]],
    user_id: int,
    username: str,
) -> str:
    """lines: (item_type, item_id, qty, unit_price) item_type in ('product','service')"""
    lines = list(lines)
    with get_connection() as conn:
        sale_number = _next_doc_number(conn, "SAL", "sales", "sale_number")
        total = 0.0
        computed: list[tuple[str, int, int, float, float]] = []
        for item_type, item_id, qty, unit_price in lines:
            if qty <= 0:
                continue
            line_total = round(qty * unit_price, 2)
            total += line_total
            computed.append((item_type, item_id, qty, unit_price, line_total))

        if not computed:
            raise ValueError("Add at least one line item")

        for item_type, item_id, qty, _, _ in computed:
            if item_type == "product":
                row = conn.execute(
                    "SELECT quantity, name FROM products WHERE id=?", (item_id,)
                ).fetchone()
                if row is None:
                    raise ValueError(f"Product #{item_id} not found")
                if row["quantity"] < qty:
                    raise ValueError(
                        f"Insufficient stock for {row['name']}: need {qty}, have {row['quantity']}"
                    )

        cur = conn.execute(
            """
            INSERT INTO sales (sale_number, customer_name, total, sale_date, user_id, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (sale_number, customer_name or None, round(total, 2), _now(), user_id, notes),
        )
        sale_id = int(cur.lastrowid)

        for item_type, item_id, qty, unit_price, line_total in computed:
            conn.execute(
                """
                INSERT INTO sale_items (sale_id, item_type, item_id, quantity, unit_price, line_total)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (sale_id, item_type, item_id, qty, unit_price, line_total),
            )
            if item_type == "product":
                conn.execute(
                    "UPDATE products SET quantity = quantity - ? WHERE id = ?",
                    (qty, item_id),
                )

    log_action(
        user_id,
        username,
        "Sale created",
        f"{sale_number} total {total:.2f}",
    )
    return sale_number


def list_sales(limit: int = 500) -> list[sqlite3.Row]:
    with get_connection() as conn:
        return list(
            conn.execute(
                """
                SELECT s.*, u.username AS seller_name
                FROM sales s
                LEFT JOIN users u ON s.user_id = u.id
                ORDER BY s.id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        )


def get_sale_items(sale_id: int) -> list[sqlite3.Row]:
    with get_connection() as conn:
        return list(
            conn.execute(
                "SELECT * FROM sale_items WHERE sale_id=? ORDER BY id",
                (sale_id,),
            ).fetchall()
        )


# --- Purchases ---


def create_purchase(
    supplier_name: str,
    notes: str,
    lines: Iterable[tuple[int, int, float]],
    user_id: int,
    username: str,
) -> str:
    """lines: (product_id, qty, unit_cost)"""
    lines = list(lines)
    with get_connection() as conn:
        purchase_number = _next_doc_number(conn, "PUR", "purchases", "purchase_number")
        total = 0.0
        computed: list[tuple[int, int, float, float]] = []
        for product_id, qty, unit_cost in lines:
            if qty <= 0:
                continue
            line_total = round(qty * unit_cost, 2)
            total += line_total
            computed.append((product_id, qty, unit_cost, line_total))

        if not computed:
            raise ValueError("Add at least one line item")

        for product_id, qty, _, _ in computed:
            row = conn.execute(
                "SELECT id FROM products WHERE id=?", (product_id,)
            ).fetchone()
            if row is None:
                raise ValueError(f"Product #{product_id} not found")

        cur = conn.execute(
            """
            INSERT INTO purchases (purchase_number, supplier_name, total, purchase_date, user_id, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                purchase_number,
                supplier_name or None,
                round(total, 2),
                _now(),
                user_id,
                notes,
            ),
        )
        purchase_id = int(cur.lastrowid)

        for product_id, qty, unit_cost, line_total in computed:
            conn.execute(
                """
                INSERT INTO purchase_items (purchase_id, product_id, quantity, unit_cost, line_total)
                VALUES (?, ?, ?, ?, ?)
                """,
                (purchase_id, product_id, qty, unit_cost, line_total),
            )
            conn.execute(
                "UPDATE products SET quantity = quantity + ? WHERE id = ?",
                (qty, product_id),
            )

    log_action(
        user_id,
        username,
        "Purchase recorded",
        f"{purchase_number} total {total:.2f}",
    )
    return purchase_number


def list_purchases(limit: int = 500) -> list[sqlite3.Row]:
    with get_connection() as conn:
        return list(
            conn.execute(
                """
                SELECT p.*, u.username AS buyer_name
                FROM purchases p
                LEFT JOIN users u ON p.user_id = u.id
                ORDER BY p.id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        )


def get_purchase_items(purchase_id: int) -> list[sqlite3.Row]:
    with get_connection() as conn:
        return list(
            conn.execute(
                """
                SELECT pi.*, pr.name AS product_name
                FROM purchase_items pi
                JOIN products pr ON pi.product_id = pr.id
                WHERE pi.purchase_id=?
                ORDER BY pi.id
                """,
                (purchase_id,),
            ).fetchall()
        )


# --- Reports & logs ---


def report_summary() -> dict[str, Any]:
    with get_connection() as conn:
        products = conn.execute(
            "SELECT COUNT(*) AS c, COALESCE(SUM(quantity * unit_price),0) AS v FROM products"
        ).fetchone()
        services = conn.execute(
            "SELECT COUNT(*) AS c FROM services"
        ).fetchone()
        sales = conn.execute(
            "SELECT COUNT(*) AS c, COALESCE(SUM(total),0) AS t FROM sales"
        ).fetchone()
        purchases = conn.execute(
            "SELECT COUNT(*) AS c, COALESCE(SUM(total),0) AS t FROM purchases"
        ).fetchone()
        return {
            "product_count": products["c"],
            "inventory_value": products["v"],
            "service_count": services["c"],
            "sale_count": sales["c"],
            "sales_total": sales["t"],
            "purchase_count": purchases["c"],
            "purchases_total": purchases["t"],
        }


def list_activity_log(limit: int = 1000) -> list[sqlite3.Row]:
    with get_connection() as conn:
        return list(
            conn.execute(
                "SELECT * FROM activity_log ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        )
