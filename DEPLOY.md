# نشر الـ API (Django) على Linux VPS

مشروع Django REST API — يعمل عبر Gunicorn خلف Nginx. ملفات لوحة الإدارة (admin) تُخدم من Nginx بعد جمعها بـ `collectstatic`.

## المتطلبات على السيرفر

- **Python 3.10+**
- **Nginx** (وكيل عكسي + خدمة الملفات الثابتة)
- **(اختياري)** PostgreSQL بدلاً من SQLite للإنتاج

---

## 1. تثبيت الحزم (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv nginx
```

---

## 2. رفع المشروع إلى السيرفر

```bash
# مثال باستخدام rsync من جهازك
rsync -avz --exclude __pycache__ --exclude "*.pyc" --exclude .env --exclude db.sqlite3 \
  /path/to/point_digital_marketing_manager_api/ user@your-vps-ip:/var/www/point_digital_marketing_manager_api/
```

أو عبر Git:

```bash
sudo mkdir -p /var/www/point_digital_marketing_manager_api
sudo chown $USER:$USER /var/www/point_digital_marketing_manager_api
git clone <your-repo-url> /var/www/point_digital_marketing_manager_api
cd /var/www/point_digital_marketing_manager_api
```

---

## 3. البيئة الافتراضية واعتماديات Python

```bash
cd /var/www/point_digital_marketing_manager_api
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4. ملف البيئة (.env) على السيرفر

```bash
nano /var/www/point_digital_marketing_manager_api/.env
```

محتوى مقترح (عدّل القيم):

```env
# مفتاح سري قوي — ولّده مرة واحدة ولا تشاركه
SECRET_KEY=your-long-random-secret-key-here

# false في الإنتاج
DEBUG=False

# نطاق السيرفر أو IP (مفصولة بفاصلة)
ALLOWED_HOSTS=api.yourdomain.com,your-vps-ip

# مفاتيح API المسموح بها (مفصولة بفاصلة) — نفس المفتاح المستخدم في تطبيق الواجهة
ALLOWED_API_KEYS=your-api-key-here
```

توليد `SECRET_KEY` عشوائي:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

---

## 5. الإعدادات من .env

المشروع يقرأ من `.env` تلقائياً: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `ALLOWED_API_KEYS`. لا حاجة لتعديل `settings.py` إن أنشأت `.env` كما في الخطوة 4.

---

## 6. قاعدة البيانات والهجرات وجمع الملفات الثابتة

```bash
cd /var/www/point_digital_marketing_manager_api
source .venv/bin/activate
python manage.py migrate
python manage.py createsuperuser   # إن احتجت مستخدماً للوحة الإدارة
python manage.py collectstatic --noinput   # مطلوب لعرض لوحة الإدارة (admin) بشكل صحيح
```

**مهم:** `collectstatic` ينسخ CSS/JS لوحة الإدارة إلى `staticfiles/`. بدونها ستظهر صفحة `/admin/` بدون تنسيق (مربعات سوداء ونص عادي). Nginx يخدم هذه الملفات من مسار `/static/` (انظر الخطوة 9).

---

## 7. تشغيل Gunicorn (اختبار سريع)

```bash
cd /var/www/point_digital_marketing_manager_api
source .venv/bin/activate
gunicorn --bind 0.0.0.0:8000 point_digital_marketing_manager_api.wsgi:application
```

بعد التأكد أن الطلبات تعمل، أوقفه (Ctrl+C) وانتقل إلى systemd.

---

## 8. خدمة systemd لتشغيل الـ API دائماً

```bash
sudo nano /etc/systemd/system/point_digital_marketing_manager_api.service
```

المحتوى:

```ini
[Unit]
Description=Point Digital Marketing Manager API (Gunicorn)
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/point_digital_marketing_manager_api
Environment="PATH=/var/www/point_digital_marketing_manager_api/.venv/bin"
ExecStart=/var/www/point_digital_marketing_manager_api/.venv/bin/gunicorn --workers 3 --bind unix:/var/www/point_digital_marketing_manager_api/gunicorn.sock point_digital_marketing_manager_api.wsgi:application

Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

**مهم:** الخدمة تعمل بالمستخدم `www-data` ويجب أن يكون له حق الكتابة في مجلد المشروع لإنشاء `gunicorn.sock`. نفّذ قبل تشغيل الخدمة:

```bash
sudo chown -R www-data:www-data /var/www/point_digital_marketing_manager_api
```

إذا رفعت المشروع كمستخدم آخر (مثلاً `deploy`) استبدل `User=www-data` و `Group=www-data` به، واستخدم نفس المستخدم في أمر `chown`.

تفعيل وتشغيل الخدمة:

```bash
sudo systemctl daemon-reload
sudo systemctl enable point_digital_marketing_manager_api
sudo systemctl start point_digital_marketing_manager_api
sudo systemctl status point_digital_marketing_manager_api
```

---

## 9. إعداد Nginx: وكيل عكسي + الملفات الثابتة (لوحة الإدارة)

Gunicorn لا يخدم الملفات الثابتة. يجب أن يخدم Nginx مسار `/static/` من مجلد `staticfiles/` حتى تظهر لوحة الإدارة (Django admin) بتنسيق صحيح.

```bash
sudo nano /etc/nginx/sites-available/point_digital_marketing_manager_api
```

المحتوى (استبدل `api.yourdomain.com`):

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    # ملفات ثابتة لوحة الإدارة (Django admin) — مطلوب لعرض CSS/JS بشكل صحيح
    location /static/ {
        alias /var/www/point_digital_marketing_manager_api/staticfiles/;
    }

    location / {
        proxy_pass http://unix:/var/www/point_digital_marketing_manager_api/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
    }

    client_max_body_size 10M;
}
```

تفعيل واختبار:

```bash
sudo ln -s /etc/nginx/sites-available/point_digital_marketing_manager_api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 10. (اختياري) HTTPS مع Let's Encrypt

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api.yourdomain.com
```

---

## 11. CORS — تأكد من النطاق الأمامي

في `settings.py` يمكنك تقييد CORS في الإنتاج بدلاً من السماح لجميع المصادر:

```python
# للإنتاج: سماح نطاق الواجهة فقط
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
]
```

مع الإبقاء على:

```python
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept", "accept-encoding", "authorization", "content-type",
    "origin", "user-agent", "x-csrftoken", "x-requested-with", "x-api-key",
]
```

---

## 12. تحديث الـ API لاحقاً

```bash
cd /var/www/point_digital_marketing_manager_api
source .venv/bin/activate
git pull   # إن كنت تستخدم Git
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput   # إن أضفت/عدّلت تطبيقات تستخدم ملفات ثابتة
sudo systemctl restart point_digital_marketing_manager_api
```

---

## ملخص الملفات والمتغيرات

| الملف/المتغير      | الوصف |
|--------------------|--------|
| `.env`             | `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `ALLOWED_API_KEYS` |
| `staticfiles/`     | مخرجات `collectstatic` — يخدمها Nginx من `/static/` |
| `gunicorn.sock`    | ملف Socket الذي ينشئه Gunicorn ويتصل به Nginx |
| `point_digital_marketing_manager_api.service` | خدمة systemd لتشغيل Gunicorn تلقائياً |

**التحقق من السجلات:**

```bash
sudo journalctl -u point_digital_marketing_manager_api -f
```

**إعادة تشغيل الـ API:**

```bash
sudo systemctl restart point_digital_marketing_manager_api
```

**إذا ظهرت لوحة الإدارة بدون تنسيق (مربعات سوداء):** تأكد من تنفيذ `collectstatic` ووجود بلوك `location /static/` في تكوين Nginx كما في الخطوة 9.
