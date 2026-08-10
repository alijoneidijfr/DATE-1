import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = "secret-key-1234"  # برای مدیریت نشست ادمین

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# ساخت دیتابیس در صورت نبودن
with get_db_connection() as conn:
    conn.execute('''CREATE TABLE IF NOT EXISTS final_date (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        selected_date TEXT,
                        selected_time TEXT,
                        cafe_name TEXT,
                        cafe_area TEXT,
                        latitude TEXT,
                        longitude TEXT,
                        phone TEXT)''')
    conn.commit()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/arrange", methods=["GET", "POST"])
def arrange():
    return render_template("arrange.html")

@app.post("/submit-final")
def submit_final():
    date = request.form.get("date")
    time = request.form.get("time")
    cafe_name = request.form.get("cafe_name")
    cafe_area = request.form.get("cafe_area")
    lat = request.form.get("lat")
    lng = request.form.get("lng")
    phone = request.form.get("phone")

    with get_db_connection() as conn:
        conn.execute("INSERT INTO final_date (selected_date, selected_time, cafe_name, cafe_area, latitude, longitude, phone) VALUES (?, ?, ?, ?, ?, ?, ?)",
                     (date, time, cafe_name, cafe_area, lat, lng, phone))
        conn.commit()
    return render_template("success.html")

# --- مسیرهای ادمین ---

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == "1234":
            session["admin_logged_in"] = True
            return redirect(url_for("admin_panel"))
        flash("رمز عبور اشتباه است.")
    return render_template("admin_login.html")

@app.route("/admin")
def admin_panel():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    
    with get_db_connection() as conn:
        bookings = conn.execute("SELECT * FROM final_date ORDER BY id DESC").fetchall()
    return render_template("admin.html", bookings=bookings)

@app.route("/admin/delete/<int:id>", methods=["POST"])
def delete_booking(id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    with get_db_connection() as conn:
        conn.execute("DELETE FROM final_date WHERE id = ?", (id,))
        conn.commit()
    return redirect(url_for("admin_panel"))

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

if __name__ == "__main__":
    app.run(debug=True)
