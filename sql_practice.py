import sqlite3
from pathlib import Path

import requests

response = requests.get(
    "https://api.practicesoftwaretesting.com/products",
    params={"page": 1},
    timeout=20,
)
assert response.status_code == 200
products = response.json()["data"]
assert products, "API nije vratio proizvode"

db_path = Path(__file__).with_name("toolshop_vezba.db")
db = sqlite3.connect(db_path)

with db:
    db.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL
        )
    """)

    # Osvezavamo lokalnu kopiju prve stranice proizvoda.
    db.execute("DELETE FROM products")

    db.executemany(
        "INSERT INTO products (id, name, price) VALUES (?, ?, ?)",
        [(p["id"], p["name"], p["price"]) for p in products],
    )

    db.execute("""
            CREATE TABLE IF NOT EXISTS product_categories (
                product_id TEXT PRIMARY KEY,
                category_name TEXT NOT NULL
            )
        """)

    db.execute("DELETE FROM product_categories")

    db.executemany(
        """
        INSERT INTO product_categories (product_id, category_name)
        VALUES (?, ?)
        """,
        [(p["id"], p["category"]["name"]) for p in products],
    )

    db.execute(
        "DELETE FROM product_categories WHERE product_id = ?",
        (products[0]["id"],),
    )

    db.execute(
        "UPDATE products SET price = ? WHERE id = ?",
        (1.00, products[0]["id"]),
    )

    rows = db.execute("""
            SELECT p.name, pc.category_name, p.price
            FROM products AS p
            LEFT JOIN product_categories AS pc
                ON p.id = pc.product_id
            WHERE pc.product_id IS NULL;
        """).fetchall()

db.close()

for name, category, price in rows:
    print(f"{name} | {category} | {price}")