import os
import sqlite3
from pathlib import Path
from flask import Flask, render_template, request

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")

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
init_db()

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
        return render_template("arrange.html", error="لطفاً تاریخ و ساعت را انتخاب کن.")
    
    # اصلاح نام قالب به cofe.html مطابق با فایل موجود در زیپ شما
    return render_template("cofe.html", date=date, time=time)

@app.post("/submit-final")
def submit_final():
    date = request.form.get("date")
    time = request.form.get("time")
    cafe_name = request.form.get("cafe_name", "")
    cafe_area = request.form.get("cafe_area", "")
    lat = request.form.get("lat", "")
    lng = request.form.get("lng", "")
    phone = request.form.get("phone", "")

    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO final_date (selected_date, selected_time, cafe_name, cafe_area, latitude, longitude, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (date, time, cafe_name, cafe_area, lat, lng, phone))
    
    return render_template("thanks.html", date=date, time=time, cafe_name=cafe_name, 
                           cafe_area=cafe_area, latitude=lat, longitude=lng, phone=phone)

@app.get("/health")
def health():
    return {"status": "ok"}, 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
