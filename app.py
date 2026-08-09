import os
import sqlite3
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "secret-key-123")

def init_db():
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS final_date (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                selected_date TEXT,
                selected_time TEXT,
                cafe_name TEXT,
                cafe_area TEXT,
                lat TEXT,
                lng TEXT
            )
        """)
init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/arrange", methods=["GET", "POST"])
def arrange():
    if request.method == "POST":
        # دریافت اطلاعات تاریخ و ساعت
        date = request.form.get("date")
        time = request.form.get("time")
        return render_template("cafe.html", date=date, time=time)
    return render_template("arrange.html")

@app.route("/submit-final", methods=["POST"])
def submit_final():
    data = request.form
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute("""
            INSERT INTO final_date (selected_date, selected_time, cafe_name, cafe_area, lat, lng)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (data['date'], data['time'], data['cafe_name'], data['cafe_area'], data['lat'], data['lng']))
    return render_template("thanks.html")

@app.get("/health")
def health():
    return {"status": "ok"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
