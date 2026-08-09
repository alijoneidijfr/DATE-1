# رزرو آنلاین دیت با Flask

## اجرای محلی

```bash
python -m venv .venv
.venv\Scripts\activate  # ویندوز
pip install -r requirements.txt
python app.py
```

سپس `http://127.0.0.1:5000` را باز کنید.

## استقرار روی Render

1. محتوای این پوشه را در ریشه یک GitHub repository آپلود کنید.
2. در Render: **New → Blueprint** و repository را انتخاب کنید.
3. در تنظیمات Environment مقدار `ADMIN_PASSWORD` را به رمز دلخواه تغییر دهید.
4. پس از Deploy، سایت در `/` و پنل در `/admin` است.

## نکته

این نسخه برای دمو طراحی شده است. SQLite روی سرویس رایگان Render پایدار نیست و ممکن است اطلاعات پس از redeploy یا restart پاک شود.
