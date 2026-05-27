from flask import (Flask, render_template, request, redirect, url_for)
from psycopg2 import pool
from dotenv import load_dotenv
import os

app = Flask(__name__)

# Database config from environment
DB_CONFIG = {
    "database": os.environ["DB_NAME"],
    "user": os.environ["DB_USER"],
    "password": os.environ["DB_PASS"],
    "host": os.environ["DB_HOST"],
    "port": os.environ["DB_PORT"],
}

# Create a connection pool
connection_pool = pool.SimpleConnectionPool(1, 10, **DB_CONFIG)


def get_conn():
    return connection_pool.getconn()


def release_conn(conn):
    connection_pool.putconn(conn)


# ---- Database setup (runs once on startup) ----
def init_db():
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS products (
                        id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                        name TEXT NOT NULL,
                        price NUMERIC(6,2) NOT NULL CHECK (price >= 0),
                        created TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                    """
                )

                # Seed data (only if table is empty)
                cur.execute("SELECT COUNT(*) FROM products;")
                count = cur.fetchone()[0]

                if count == 0:
                    cur.execute(
                        """
                        INSERT INTO products (name, price)
                        VALUES
                            ('Apple', 1.99),
                            ('Orange', 0.99),
                            ('Pear', 0.79),
                            ('Banana', 0.59);
                        """
                    )
    finally:
        release_conn(conn)


init_db()

# ---- Routes ----

@app.route('/')
def index():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM products ORDER BY id')
            data = cur.fetchall()
        return render_template('index.html', data=data)
    finally:
        release_conn(conn)


@app.route('/create', methods=['POST'])
def create():
    name = request.form['name']
    price = request.form['price']

    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    'INSERT INTO products (name, price) VALUES (%s, %s)',
                    (name, price)
                )
    finally:
        release_conn(conn)

    return redirect(url_for('index'))


@app.route('/update', methods=['POST'])
def update():
    name = request.form['name']
    price = request.form['price']
    id = request.form['id']

    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    'UPDATE products SET name=%s, price=%s, updated_at=CURRENT_TIMESTAMP WHERE id=%s',
                    (name, price, id)
                )
    finally:
        release_conn(conn)

    return redirect(url_for('index'))


@app.route('/delete', methods=['POST'])
def delete():
    id = request.form['id']

    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM products WHERE id=%s', (id,))
    finally:
        release_conn(conn)

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)