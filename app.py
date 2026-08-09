import os
import sqlite3
from pathlib import Path

from flask import Flask, render_template, request


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "change-this-secret-key"
)


def get_db_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS final_date (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                selected_date TEXT NOT NULL,
                selected_time TEXT NOT NULL,
                cafe_name TEXT NOT NULL DEFAULT '',
                cafe_area TEXT NOT NULL DEFAULT '',
                latitude TEXT NOT NULL DEFAULT '',
                longitude TEXT NOT NULL DEFAULT '',
                phone TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # افزودن ستون phone به دیتابیس‌های قدیمی
        columns = connection.execute(
            "PRAGMA table_info(final_date)"
        ).fetchall()

        column_names = [column["name"] for column in columns]

        if "phone" not in column_names:
            connection.execute(
                "ALTER TABLE final_date ADD COLUMN phone TEXT NOT NULL DEFAULT ''"
            )


init_db()


@app.get("/")
def index():
    return render_template("index.html")


@app.route("/arrange", methods=["GET", "POST"])
def arrange():
    if request.method == "GET":
        return render_template("arrange.html")

    selected_date = request.form.get("date", "").strip()
    selected_time = request.form.get("time", "").strip()

    if not selected_date or not selected_time:
        return render_template(
            "arrange.html",
            error="لطفاً تاریخ و ساعت را انتخاب کن."
        )

    return render_template(
        "cofe.html",
        date=selected_date,
        time=selected_time
    )


@app.post("/submit-final")
def submit_final():
    selected_date = request.form.get("date", "").strip()
    selected_time = request.form.get("time", "").strip()

    # اطلاعات کافه و لوکیشن اختیاری هستند
    cafe_name = request.form.get("cafe_name", "").strip()
    cafe_area = request.form.get("cafe_area", "").strip()
    latitude = request.form.get("lat", "").strip()
    longitude = request.form.get("lng", "").strip()

    phone = request.form.get("phone", "").strip()

    if not selected_date or not selected_time:
        return render_template(
            "arrange.html",
            error="لطفاً تاریخ و ساعت را انتخاب کن."
        )

    if not phone:
        return render_template(
            "cofe.html",
            date=selected_date,
            time=selected_time,
            error="لطفاً 
