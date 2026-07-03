sms_gateway/
├── app/ # تمام کدهای مربوط به منطق برنامه
│ ├── main.py # تعریف وب‌سرویس‌ها و پیکربندی اصلی FastAPI
│ ├── config.py # تنظیمات محیطی و متغیرهای سراسری دیتابیس
│ ├── database.py # راه‌اندازی SQLAlchemy و کانکشن‌پول دیتابیس
│ ├── models.py # تعریف مدل‌های دیتابیس (SQLAlchemy ORM)
│ ├── schemas.py # مدل‌های اعتبارسنجی داده‌های ورودی (Pydantic)
│ ├── services/ # منطق بیزینس و کدهای عملیاتی
│ │ ├── adapters.py # آداپتورهای درگاه‌ها بر اساس الگوی Adapter
│ │ ├── routing.py # موتور مسیریابی هوشمند و جابه‌جایی خطا (Failover)
│ │ └── otp.py # کدهای تایید موقت با پشتیبانی از کش Redis
├── .gitignore # فایل نادیده‌گرفتن فایل‌های اضافی برای گیت
├── requirements.txt # لیست کتابخانه‌ها و وابستگی‌ها
└── README.md # راهنما و مستندات پروژه
ابزارها و نیازمند‌ی‌های فنی (Tech Stack)
Language: Python 3.10+
Framework: FastAPI (0.110.0)
ORM: SQLAlchemy (2.0.28)
Driver: Psycopg2-binary (2.9.9)
Database: PostgreSQL (به همراه استفاده بومی از انواع داده JSONB و UUID)
Cache: Redis (سیستم OTP دومنظوره با قابلیت تغییر خودکار به حافظه لوکال پایتون)
راهنمای نصب و راه‌اندازی پروژه
۱. گام اول: ساخت پایگاه‌داده خام در PostgreSQL
قبل از راه‌اندازی پروژه، باید دیتابیس مربوط به سیستم را در پایگاه‌داده PostgreSQL خود ایجاد کنید. با ابزارهایی مانند pgAdmin یا psql دستور زیر را اجرا کنید:
code
SQL
CREATE DATABASE sms_gateway_db;
۲. گام دوم: ساخت محیط مجازی (Virtual Environment)
code Bash
python -m venv venv
۳. گام سوم: فعال‌سازی محیط مجازی
در ویندوز (Git Bash):
code Bash
source venv/Scripts/activate
در ویندوز (CMD):
code Cmd
venv\Scripts\activate
در لینوکس یا مک:
code Bash
source venv/bin/activate
۴. گام چهارم: نصب پکیج‌ها و پیش‌نیازها
code Bash
pip install -r requirements.txt
۵. گام پنجم: بررسی اطلاعات اتصال در فایل تنظیمات
فایل app/config.py را باز کرده و در صورت تفاوت در نام کاربری یا پسورد پایگاه‌داده PostgreSQL سیستم خود، اطلاعات بخش اتصال را ویرایش کنید:
postgresql://USER:PASSWORD@localhost:5432/sms_gateway_db
۶. گام ششم: اجرای وب‌سرور پروژه
code Bash
uvicorn app.main:app --reload --port 8000
با اولین استارت برنامه، تمام جداول، روابط کلید خارجی (Foreign Keys) و ساختار دیتابیس به صورت کاملاً خودکار بر روی پایگاه داده PostgreSQL شما ساخته خواهد شد.
راهنمای تست پروژه با پنل تعاملی (Swagger UI)
پس از اجرای وب‌سرور، به آدرس زیر بروید تا وارد کنترل پنل تست مستقیم وب‌سرویس‌ها شوید:
http://127.0.0.1:8000/docs
۱. احراز هویت (Authorize)
روی دکمه سبز رنگ Authorize در بالای سمت راست صفحه کلیک کنید.
کلید امنیتی پیش‌فرض زیر را وارد کرده و دکمه Authorize را بزنید:
SECRET_INTEGRATION_KEY
با بستن پاپ‌آپ، قفل‌های امنیتی تمام اندپوینت‌ها فعال خواهند شد.
۲. ثبت یک درگاه شبیه‌ساز (Mock Provider)
بخش POST /api/v1/providers را باز کرده و روی Try it out کلیک کنید.
کد زیر را در بخش بدنه قرار دهید و دکمه آبی Execute را فشار دهید تا درگاه تستی با فرمت ساختاریافته در فیلد JSONB دیتابیس ذخیره شود:
code
JSON
{
"name": "Magfa Core Gateway",
"adapter_type": "magfa",
"config": {
"api_key": "MOCK_KEY_123"
},
"sender_number": "300090",
"priority": 1
}
۳. ارسال پیامک با موتور مسیریابی و مدیریت خطا
بخش POST /api/v1/send را باز کرده و روی Try it out کلیک کنید.
کد نمونه زیر را در بدنه درخواست جایگزین کرده و دکمه Execute را بزنید:
code
JSON
{
"recipient": "09121234567",
"body": "درگاه پیامکی هوشمند شما با موفقیت بر بستر پایگاه داده PostgreSQL فعال شد.",
"message_type": "info"
}
پاسخ موفقیت‌آمیز بودن تراکنش را دریافت خواهید کرد و پیام به همراه شناسه UUID یکتا در جدول مربوطه ذخیره می‌شود.
