# הגדרת HTTPS - LinkUp Project

## סקירה כללית

HTTPS הוא **חובה בפרודקשן** אבל **אופציונלי בפיתוח מקומי**. מדריך זה מסביר איך להגדיר HTTPS בשני המקרים.

---

## 🏠 פיתוח מקומי (Localhost)

### אפשרות 1: HTTP (מומלץ לפיתוח)

בפיתוח מקומי, **HTTP זה בסדר** כי:
- `localhost` הוא בטוח יחסית (לא עובר באינטרנט)
- פשוט יותר - אין צורך ב-certificates
- מהיר יותר - אין overhead של TLS

**השימוש:**
- Backend: `http://localhost:8000`

### אפשרות 2: HTTPS בפיתוח (אם רוצה)

אם אתה רוצה לבדוק HTTPS גם בפיתוח מקומי, השתמש ב-uvicorn עם SSL או ב-reverse proxy מקומי (למשל Caddy/Nginx) עם self-signed certificate.

---

## 🚀 פרודקשן (Production)

בפרודקשן, **HTTPS הוא חובה** כי:
- הגנה על נתונים (passwords, tokens, מידע אישי)
- Google ו-browsers דורשים HTTPS
- SEO - Google מעדיף HTTPS

### ארכיטקטורה מומלצת

```
Internet → Cloudflare/Nginx (HTTPS) → Backend (HTTP)
```

**למה?**
- **Cloudflare/Nginx** מטפלים ב-TLS termination
- **Backend** מקבל HTTP פנימי (פשוט יותר)

### שלב 1: הגדרת Reverse Proxy (Cloudflare או Nginx)

#### אופציה A: Cloudflare (הכי פשוט)

1. הוסף את הדומיין שלך ל-Cloudflare
2. הפעל "SSL/TLS" → "Full" mode
3. Cloudflare יגן עליך אוטומטית

#### אופציה B: Nginx עם Let's Encrypt

```nginx
# /etc/nginx/sites-available/linkup-api
server {
    listen 443 ssl http2;
    server_name api.linkup.co.il;

    # Let's Encrypt certificates (נוצרים אוטומטית עם certbot)
    ssl_certificate /etc/letsencrypt/live/api.linkup.co.il/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.linkup.co.il/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location / {
        proxy_pass http://localhost:8000;  # Backend
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;  # חשוב!
        proxy_set_header X-Forwarded-Host $host;
    }
}

# Redirect HTTP → HTTPS
server {
    listen 80;
    server_name api.linkup.co.il;
    return 301 https://$server_name$request_uri;
}
```

**התקנת Let's Encrypt:**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.linkup.co.il
```

### שלב 2: עדכון Backend Configuration

ב-`.env` של הפרודקשן:

```env
FORCE_HTTPS_REDIRECT=true
FRONTEND_URL=https://linkup.co.il
API_PUBLIC_URL=https://api.linkup.co.il
```

**מה זה עושה?**
- `FORCE_HTTPS_REDIRECT=true` - מפנה כל בקשה HTTP ל-HTTPS (301 redirect)
- Backend מזהה HTTPS לפי `X-Forwarded-Proto: https` שהפרוקסי שולח

### שלב 3: עדכון CORS (Backend)

ב-`.env` או ב-config, הגדר `CORS_ORIGINS` ל-production domains (למשל `https://linkup.co.il,https://www.linkup.co.il`).

---

## 🔒 Security Headers

הפרויקט כבר כולל security headers אוטומטית:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Strict-Transport-Security` (HSTS) - רק על HTTPS

---

## ✅ Checklist לפרודקשן

- [ ] Reverse proxy (Cloudflare/Nginx) מוגדר עם HTTPS
- [ ] `FORCE_HTTPS_REDIRECT=true` ב-`.env`
- [ ] `FRONTEND_URL` ו-`API_PUBLIC_URL` מוגדרים ל-HTTPS
- [ ] CORS_ORIGINS מעודכן ל-production domains
- [ ] Let's Encrypt certificates מוגדרים (אם לא משתמשים ב-Cloudflare)
- [ ] בדיקת HTTPS: `curl -I https://api.linkup.co.il`
- [ ] בדיקת HTTP redirect: `curl -I http://api.linkup.co.il` (צריך להחזיר 301)

---

## 🐛 Troubleshooting

### "Mixed Content" error בדפדפן

**בעיה:** Frontend מנסה לגשת ל-HTTP מ-HTTPS page.

**פתרון:** ודא שכל ה-API calls משתמשים ב-`https://` ולא `http://`.

### CORS errors עם credentials

**בעיה:** `credentials: true` לא עובד עם `origins: ["*"]`.

**פתרון:** שנה ל-origins ספציפיים (ראו לעיל).

### Self-signed certificate warning בפיתוח

**זה נורמלי!** Self-signed certificates לא מאומתים על ידי browsers. בפרודקשן, השתמש ב-Let's Encrypt או Cloudflare.

---

## 📚 משאבים נוספים

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Cloudflare SSL/TLS Guide](https://developers.cloudflare.com/ssl/)
- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/advanced/security/)
