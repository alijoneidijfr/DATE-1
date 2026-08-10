import os
import sqlite3
from pathlib import Path
from datetime import date as gregorian_date
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "dev-secret-key"
)

ADMIN_PASSWORD = os.environ.get(
    "ADMIN_PASSWORD",
    "1234"
)


def get_db_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS final_date (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                selected_date TEXT NOT NULL,
                selected_time TEXT NOT NULL,
                cafe_name TEXT DEFAULT '',
                cafe_area TEXT DEFAULT '',
                latitude TEXT DEFAULT '',
                longitude TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        columns = conn.execute(
            "PRAGMA table_info(final_date)"
        ).fetchall()

        column_names = [column["name"] for column in columns]

        required_columns = {
            "cafe_name": "TEXT DEFAULT ''",
            "cafe_area": "TEXT DEFAULT ''",
            "latitude": "TEXT DEFAULT ''",
            "longitude": "TEXT DEFAULT ''",
            "phone": "TEXT DEFAULT ''"
        }

        for column_name, column_type in required_columns.items():
            if column_name not in column_names:
                conn.execute(
                    f"ALTER TABLE final_date "
                    f"ADD COLUMN {column_name} {column_type}"
                )

        conn.commit()


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

    if gd > 365:
        gd -= 365
        gy += 1

    month_days = [
        31, 28, 31, 30, 31, 30,
        31, 31, 30, 31, 30, 31
    ]

    if gy % 4 == 0 and (
        gy % 100 != 0 or gy % 400 == 0
    ):
        month_days[1] = 29

    gm = 1

    while gd > month_days[gm - 1]:
        gd -= month_days[gm - 1]
        gm += 1

    return gy, gm, gd


def get_weekday_name(jalali_date):
    try:
        parts = jalali_date.replace("-", "/").split("/")

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
            "یکشنبه"
        ]

        return weekdays[weekday_index]

    except Exception:
        return ""


@app.get("/")
def index():
    return render_template("index.html")


@app.route("/arrange", methods=["GET", "POST"])
def arrange():
    if request.method == "GET":
        return render_template("arrange.html")

    date = request.form.get("date", "").strip()
    time = request.form.get("time", "").strip()

    if not date or not time:
        return render_template(
            "arrange.html",
            error="لطفاً تاریخ و ساعت را انتخاب کن."
        )

    return render_template(
        "cofe.html",
        date=date,
        time=time
    )


@app.post("/submit-final")
def submit_final():
    date = request.form.get("date", "").strip()
    time = request.form.get("time", "").strip()
    cafe_name = request.form.get("cafe_name", "").strip()
    cafe_area = request.form.get("cafe_area", "").strip()

    # مختصات دقیقاً از همین نام‌ها دریافت می‌شوند
    lat = request.form.get("lat", "").strip()
    lng = request.form.get("lng", "").strip()

    phone = request.form.get("phone", "").strip()

    if not date or not time:
        return render_template(
            "arrange.html",
            error="لطفاً تاریخ و ساعت را انتخاب کن."
        )

    if not cafe_name or not cafe_area:
        return render_template(
            "cofe.html",
            date=date,
            time=time,
            error="لطفاً نام کافه و محله را وارد کن."
        )

    # جلوگیری از ثبت رزرو بدون انتخاب نقطه روی نقشه
    if not lat or not lng:
        return render_template(
            "cofe.html",
            date=date,
            time=time,
            error="لطفاً برای ثبت لوکیشن، روی نقشه کلیک کن."
        )

    with get_db_connection() as conn:
        conn.execute("""
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
        """, (
            date,
            time,
            cafe_name,
            cafe_area,
            lat,
            lng,
            phone
        ))

        conn.commit()

    weekday = get_weekday_name(date)

    return render_template(
        "thanks.html",
        date=date,
        time=time,
        weekday=weekday,
        cafe_name=cafe_name,
        cafe_area=cafe_area,
        latitude=lat,
        longitude=lng,
        phone=phone
    )


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))

        return view_func(*args, **kwargs)

    return wrapper


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None

    if request.method == "POST":
        password = request.form.get(
            "password",
            ""
        ).strip()

        if password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_panel"))

        error = "رمز عبور اشتباه است."

    return render_template(
        "admin_login.html",
        error=error
    )


@app.get("/admin")
@admin_required
def admin_panel():
    with get_db_connection() as conn:
        bookings = conn.execute("""
            SELECT
                id,
                cafe_name AS name,
                phone,
                selected_date AS booking_date,
                selected_time AS booking_time,
                cafe_area,
                latitude,
                longitude,
                created_at
            FROM final_date
            ORDER BY id DESC
        """).fetchall()

    return render_template(
        "admin.html",
        bookings=bookings
    )


@app.post("/admin/logout")
@admin_required
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.post("/admin/delete/<int:booking_id>")
@admin_required
def delete_booking(booking_id):
    with get_db_connection() as conn:
        conn.execute(
            "DELETE FROM final_date WHERE id = ?",
            (booking_id,)
        )
        conn.commit()

    return redirect(url_for("admin_panel"))


@app.get("/health")
def health():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    port = int(
        os.environ.get("PORT", 5000)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
