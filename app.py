from flask import Flask, render_template, request, redirect, session
import sqlite3
from pathlib import Path
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "secret_key_123")

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database.db"


def get_db_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute(
        "CREATE TABLE IF NOT EXISTS bookings ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "name TEXT, "
        "phone TEXT, "
        "date TEXT, "
        "time TEXT)"
    )
    conn.commit()
    conn.close()


init_db()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/booking")
def booking():
    return render_template("booking.html")


@app.route("/book", methods=["POST"])
def book():
    name = request.form.get("name")
    phone = request.form.get("phone")
    date = request.form.get("date")
    time = request.form.get("time")

    if not all([name, phone, date, time]):
        return render_template("error.html", error="لطفاً همه فیلدها را تکمیل کنید."), 400

    if ":" not in time:
        return render_template("error.html", error="فرمت زمان نامعتبر است."), 400

    try:
        hour = int(time.split(":", 1)[0])
    except (ValueError, TypeError):
        return render_template("error.html", error="فرمت زمان نامعتبر است."), 400

    if hour < 16 or hour > 22:
        return render_template("error.html", error="خطا: فقط بین ساعت ۱۶ تا ۲۲ امکان رزرو وجود دارد."), 400

    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO bookings (name, phone, date, time) VALUES (?, ?, ?, ?)",
            (name, phone, date, time)
        )
        conn.commit()
        conn.close()
    except sqlite3.Error:
        return render_template("error.html", error="خطا در ثبت رزرو. لطفاً دوباره تلاش کنید."), 500

    return render_template(
        "success.html",
        name=name,
        booking_date=date,
        booking_time=time
    )


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        password = request.form.get("password")
        if password == ADMIN_PASSWORD:
            session["logged_in"] = True
        else:
            return render_template("admin_login.html", error="رمز عبور اشتباه است")

    if not session.get("logged_in"):
        return render_template("admin_login.html")

    try:
        conn = get_db_connection()
        bookings = conn.execute("SELECT * FROM bookings ORDER BY id DESC").fetchall()
        conn.close()
    except sqlite3.Error:
        return render_template("error.html", error="خطا در دریافت اطلاعات رزروها."), 500

    return render_template("admin.html", bookings=bookings)


@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    if not session.get("logged_in"):
        return redirect("/admin")

    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM bookings WHERE id = ?", (id,))
        conn.commit()
        conn.close()
    except sqlite3.Error:
        return render_template("error.html", error="خطا در حذف رزرو."), 500

    return redirect("/admin")


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect("/admin")


@app.route("/health")
def health():
    return "ok", 200


if __name__ == "__main__":
    app.run(debug=True)
