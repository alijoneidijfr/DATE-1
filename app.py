import os
import sqlite3
from pathlib import Path

from flask import Flask, render_template, request

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "secret-key-123")


def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS final_date (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                selected_date TEXT,
                selected_time TEXT,
                cafe_name TEXT,
                cafe_area TEXT,
                lat TEXT,
                lng TEXT
            )
            """
        )


init_db()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/arrange", methods=["GET", "POST"])
def arrange():
    if request.method == "POST":
        date = request.form.get("date")
        time = request.form.get("time")
        return render_template("cofe.html", date=date, 
