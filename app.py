import os
from flask import Flask, render_template

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-key")


# این‌ها را هر وقت خواستی عوض کن
DATE_TEXT = "1403/05/20"
TIME_TEXT = "19:30"


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/date-time")
def date_time():
    return render_template(
        "date_time.html",
        date_text=DATE_TEXT,
        time_text=TIME_TEXT,
    )


@app.get("/location")
def location():
    return render_template("location.html")


@app.get("/health")
def health():
    return {"status": "ok"}, 200


@app.errorhandler(404)
def not_found(error):
    return render_template("error.html", message="صفحه‌ای که دنبالش هستی پیدا نشد."), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
