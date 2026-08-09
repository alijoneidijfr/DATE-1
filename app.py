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
                cafe_name TEXT NOT NULL,
                cafe_area TEXT NOT NULL,
                latitude TEXT NOT NULL,
                longitude TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
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
    cafe_name = request.form.get("cafe_name", "").strip()
    cafe_area = request.form.get("cafe_area", "").strip()
    latitude = request.form.get("lat", "").strip()
    longitude = request.form.get("lng", "").strip()

    if not all(
        (
            selected_date,
            selected_time,
            cafe_name,
            cafe_area,
            latitude,
            longitude,
        )
    ):
        return render_template(
            "cofe.html",
            date=selected_date,
            time=selected_time,
            error="لطفاً همه اطلاعات را کامل کن و روی نقشه هم انتخاب کن."
        )

    with get_db_connection() as connection:
        connection.execute(
            """
            INSERT INTO final_date
            (
                selected_date,
                selected_time,
                cafe_name,
                cafe_area,
                latitude,
                longitude
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                selected_date,
                selected_time,
                cafe_name,
                cafe_area,
                latitude,
                longitude,
            ),
        )

    return render_template(
        "thanks.html",
        date=selected_date,
        time=selected_time,
        cafe_name=cafe_name,
        cafe_area=cafe_area,
        latitude=latitude,
        longitude=longitude,
    )


@app.get("/health")
def health():
    return {"status": "ok"}, 200


@app.errorhandler(404)
def not_found(error):
    return render_template(
        "error.html",
        message="صفحه‌ای که دنبالش هستی پیدا نشد."
    ), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
