import os
import sqlite3
from pathlib import Path
from datetime import date as gregorian_date

from flask import Flask, render_template, request


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database.db"

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "dev-secret-key"
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

        required_columns = {
            "cafe_name": "TEXT NOT NULL DEFAULT ''",
            "cafe_area": "TEXT NOT NULL DEFAULT ''",
            "latitude": "TEXT NOT NULL DEFAULT ''",
            "longitude": "TEXT NOT NULL DEFAULT ''",
            "phone": "TEXT NOT NULL DEFAULT ''",
        }

        columns = connection.execute(
            "PRAGMA table_info(final_date)"
        ).fetchall()

        existing_columns = {
            column["name"] for column in columns
        }

        for column_name, column_definition in required_columns.items():
            if column_name not in existing_columns:
                connection.execute(
                    f"""
                    ALTER TABLE final_date
                    ADD COLUMN {column_name} {column_definition}
                    """
                )


init_db()


def jalali_to_gregorian(jy, jm, jd):
    jy += 1595

    days = (
        -355668
        + (365 * jy)
        + ((jy // 33) * 8)
        + (((jy % 33) + 3) // 4)
        + jd
    )

    if jm < 7:
        days += (jm - 1) * 31
    else:
        days += ((jm - 7) * 30) + 186

    gy = 400 * (days // 146097)
    days %= 146097

    if days > 36524:
        days -= 1
        gy += 100 * (days // 36524)
        days %= 36524

        if days >= 365:
            days += 1

    gy += 4 * (days // 1461)
    days %= 1461

    if days > 365:
        gy += (days - 1) // 365
        days = (days - 1) % 365

    gd = days + 1

    month_days = [
        31, 28, 31, 30, 31, 30,
        31, 31, 30, 31, 30, 31
    ]

    if gy % 4 == 0 and (gy % 100 != 0 or gy % 400 == 0):
        month_days[1] = 29

    gm = 1

    while gm <= 12 and gd > month_days[gm - 1]:
        gd -= month_days[gm - 1]
        gm += 1

    return gy, gm, gd


def get_weekday_name(jalali_date):
    try:
        normalized_date = (
            jalali_date
            .replace("-", "/")
            .replace("۰", "0")
            .replace("۱", "1")
            .replace("۲", "2")
            .replace("۳", "3")
            .replace("۴", "4")
            .replace("۵", "5")
            .replace("۶", "6")
            .replace("۷", "7")
            .replace("۸", "8")
            .replace("۹", "9")
        )

        parts = normalized_date.split("/")

        if len(parts) != 3:
            return ""

        jy, jm, jd = map(int, parts)

        gy, gm, gd = jalali_to_gregorian(jy, jm, jd)

        weekday_index = gregorian_date(
            gy,
            gm,
            gd
        ).weekday()

        weekdays = [
            "دوشنبه",
            "سه‌شنبه",
            "چهارشنبه",
            "پنجشنبه",
            "جمعه",
            "شنبه",
            "یکشنبه",
        ]

        return weekdays[weekday_index]

    except (ValueError, TypeError, IndexError):
        return ""


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

    phone = request.form.get("phone", "").strip()

    if not selected_date or not selected_time:
        return render_template(
            "arrange.html",
            error="لطفاً تاریخ و ساعت را انتخاب کن."
        )

    if not cafe_name or not cafe_area:
        return render_template(
            "cofe.html",
            date=selected_date,
            time=selected_time,
            error="لطفاً نام کافه و محله را وارد کن."
        )

    with get_db_connection() as connection:
        connection.execute(
            """
            INSERT INTO final_date (
                selected_date,
                selected_time,
                cafe_name,
                cafe_area,
                latitude,
                longitude,
                phone
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                selected_date,
                selected_time,
                cafe_name,
                cafe_area,
                latitude,
                longitude,
                phone,
            )
        )

    weekday = get_weekday_name(selected_date)

    return render_template(
        "thanks.html",
        date=selected_date,
        time=selected_time,
        weekday=weekday,
        cafe_name=cafe_name,
        cafe_area=cafe_area,
        latitude=latitude,
        longitude=longitude,
        phone=phone,
    )


@app.get("/health")
def health():
    return {
        "status": "ok"
    }, 200


@app.errorhandler(404)
def page_not_found(error):
    return render_template(
        "error.html",
        message="صفحه موردنظر پیدا نشد."
    ), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
