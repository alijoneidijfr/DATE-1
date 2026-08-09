import os
import sqlite3
from pathlib import Path
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database.db"

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "0200899481")


def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


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

        # Migration ساده برای دیتابیس‌های قدیمی
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(final_date)").fetchall()}
        if "phone" not in columns:
            conn.execute("ALTER TABLE final_date ADD COLUMN phone TEXT DEFAULT ''")
        if "cafe_name" not in columns:
            conn.execute("ALTER TABLE final_date ADD COLUMN cafe_name TEXT DEFAULT ''")
        if "cafe_area" not in columns:
            conn.execute("ALTER TABLE final_date ADD COLUMN cafe_area TEXT DEFAULT ''")
        if "latitude" not in columns:
            conn.execute("ALTER TABLE final_date ADD COLUMN latitude TEXT DEFAULT ''")
        if "longitude" not in columns:
            conn.execute("ALTER TABLE final_date ADD COLUMN longitude TEXT DEFAULT ''")

        conn.commit()


init_db()


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return view_func(*args, **kwargs)
    return wrapper


@app.get("/")
def index():
    return render_template("index.html")


@app.route("/arrange", methods=["GET", "POST"])
def arrange():
    error = None

    if request.method == "POST":
        date = request.form.get("date", "").strip()
        time = request.form.get("time", "").strip()

        if not date or not time:
            error = "لطفاً تاریخ و ساعت را کامل انتخاب کن."
            return render_template("arrange.html", error=error)

        return render_template("cofe.html", date=date, time=time)

    return render_template("arrange.html")


@app.post("/submit-final")
def submit_final():
    date = request.form.get("date", "").strip()
    time = request.form.get("time", "").strip()
    cafe_name = request.form.get("cafe_name", "").strip()
    cafe_area = request.form.get("cafe_area", "").strip()
    lat = request.form.get("latitude", "").strip()
    lng = request.form.get("longitude", "").strip()
    phone = request.form.get("phone", "").strip()

    if not date or not time or not cafe_name or not cafe_area:
        return render_template("error.html", error="اطلاعات ناقص است.")

    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO final_date
            (selected_date, selected_time, cafe_name, cafe_area, latitude, longitude, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (date, time, cafe_name, cafe_area, lat, lng, phone))
        conn.commit()

    return render_template(
        "thanks.html",
        date=date,
        time=time,
        cafe_name=cafe_name,
        cafe_area=cafe_area,
        latitude=lat,
        longitude=lng,
        phone=phone
    )


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None

    if request.method == "POST":
        password = request.form.get("password", "").strip()

        if password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_panel"))
        else:
            error = "رمز عبور اشتباه است."

    return render_template("admin_login.html", error=error)


@app.get("/admin")
@admin_required
def admin_panel():
    with get_db_connection() as conn:
        bookings = conn.execute("""
            SELECT
                id,
                cafe_name AS name,
                selected_date AS booking_date,
                selected_time AS booking_time,
                phone,
                cafe_area,
                latitude,
                longitude,
                created_at
            FROM final_date
            ORDER BY id DESC
        """).fetchall()

    return render_template("admin.html", bookings=bookings)


@app.post("/admin/logout")
@admin_required
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.post("/admin/delete/<int:booking_id>")
@admin_required
def delete_booking(booking_id):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM final_date WHERE id = ?", (booking_id,))
        conn.commit()

    return redirect(url_for("admin_panel"))


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(debug=True)
