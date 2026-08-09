import os
import sqlite3
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-key")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")


def get_db_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                booking_date TEXT NOT NULL,
                booking_time TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


init_db()


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)

    return wrapped_view


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/book")
def book():
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    booking_date = request.form.get("date", "").strip()
    booking_time = request.form.get("time", "").strip()

    if not all((name, phone, booking_date, booking_time)):
        flash("همهٔ فیلدها را کامل کن.", "error")
        return redirect(url_for("index"))

    try:
        hour = int(booking_time.split(":", 1)[0])
    except (ValueError, IndexError):
        flash("ساعت انتخاب‌شده معتبر نیست.", "error")
        return redirect(url_for("index"))

    if hour < 16 or hour > 22:
        flash("رزرو فقط بین ساعت ۱۶:۰۰ تا ۲۲:۰۰ امکان‌پذیر است.", "error")
        return redirect(url_for("index"))

    with get_db_connection() as connection:
        conflict = connection.execute(
            "SELECT id FROM bookings WHERE booking_date = ? AND booking_time = ?",
            (booking_date, booking_time),
        ).fetchone()
        if conflict:
            flash("این روز و ساعت قبلاً رزرو شده است؛ زمان دیگری انتخاب کن.", "error")
            return redirect(url_for("index"))

        connection.execute(
            """
            INSERT INTO bookings (name, phone, booking_date, booking_time, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, phone, booking_date, booking_time, datetime.now().isoformat(timespec="seconds")),
        )

    return render_template("success.html", name=name, booking_date=booking_date, booking_time=booking_time)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("is_admin"):
        return redirect(url_for("admin"))

    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect(url_for("admin"))
        flash("رمز عبور نادرست است.", "error")

    return render_template("admin_login.html")


@app.get("/admin")
@admin_required
def admin():
    with get_db_connection() as connection:
        bookings = connection.execute(
            "SELECT * FROM bookings ORDER BY booking_date ASC, booking_time ASC"
        ).fetchall()
    return render_template("admin.html", bookings=bookings)


@app.post("/admin/bookings/<int:booking_id>/delete")
@admin_required
def delete_booking(booking_id):
    with get_db_connection() as connection:
        connection.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
    flash("رزرو حذف شد.", "success")
    return redirect(url_for("admin"))


@app.post("/admin/logout")
@admin_required
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

@app.get("/health")
def health():
    return {"status": "ok"}, 200


@app.errorhandler(404)
def not_found(error):
    return render_template("error.html", message="صفحه‌ای که دنبالش هستی پیدا نشد."), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
