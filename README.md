# Hurtl355 — Portfolio Website & Admin Panel

Flask + SQLAlchemy portfolio with a full admin panel (works, pricing, testimonials,
messages, site settings). Production stack, all on free tiers:

| Piece | Service | Why |
|---|---|---|
| App (Flask) | **Render** web service | runs Python |
| Database | **Neon** Postgres | free, survives redeploys |
| Uploaded media | **Cloudflare R2** | Render's disk is wiped on every deploy |
| Domain / DNS (later) | Cloudflare | optional |

## Folder layout

```
app/                Flask package (models, blueprints, templates, static)
wsgi.py             production entry point  (gunicorn wsgi:app)
run.py              local dev entry point   (python run.py)
seed.py             sample content + admin user for a FRESH database
scripts/            one-time helpers: migrate data, set admin password, upload media
render.yaml         Render blueprint
.env.example        copy to .env locally (never commit .env)
```

## Run locally

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # then edit SECRET_KEY and ADMIN_PASSWORD
python seed.py              # only for a brand-new empty database
python run.py               # http://127.0.0.1:5000   admin: /admin
```

## Deploy (free)

### 1. Database — Neon
1. Create a project at neon.tech and copy the **connection string** (it contains `sslmode=require`).
2. From this folder, in PowerShell:
   ```powershell
   $env:DATABASE_URL = "postgresql://...your neon string..."
   python scripts/migrate_sqlite_to_postgres.py instance/hurtl355.db
   python scripts/set_admin_password.py
   ```
   The first copies your existing works, pricing, testimonials and settings. The second sets a
   **new strong admin password** (the old one was the default `hurtl355admin`).

### 2. Media — Cloudflare R2
1. Cloudflare dashboard → R2 → create bucket (e.g. `hurtl355-media`) → enable the **public
   `r2.dev` URL** (or connect a domain).
2. R2 → Manage API tokens → create a token with *Object Read & Write* → note the Access Key ID,
   Secret, and S3 endpoint (`https://<account>.r2.cloudflarestorage.com`).
3. Put the five `R2_*` values in your local `.env`, then:
   ```powershell
   python scripts/upload_media_to_r2.py
   ```

### 3. App — Render
1. Push this folder to GitHub (see below).
2. Render → New → **Blueprint** → select the repo. It reads `render.yaml`.
3. Fill the prompted variables: `DATABASE_URL` (Neon) and the five `R2_*` values.
   `SECRET_KEY` is generated for you.
4. Open the `onrender.com` URL. Admin is at `/admin`.

### 4. Keep it awake (optional)
Free Render services sleep after ~15 min idle (first visit then takes 30–60 s). A free
UptimeRobot monitor pinging `/healthz` every 5 min avoids that.

## Pushing to GitHub

`.gitignore` already excludes `venv/`, `.env`, `instance/*.db`, `node_modules/` and caches.
Never commit `.env` or the SQLite file (it contains your admin hash and visitor emails).

## Environment variables

| Name | Needed | Notes |
|---|---|---|
| `SECRET_KEY` | production | app refuses to start in production without a real one |
| `DATABASE_URL` | production | Neon string; `sqlite:///hurtl355.db` locally |
| `FLASK_ENV` | — | `production` on Render (set by render.yaml) |
| `R2_ENDPOINT`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`, `R2_PUBLIC_URL` | production | all five or none; none = files saved on local disk |
| `TRUSTED_PROXIES` | — | number of proxies in front (default 1; use 2 if Cloudflare proxies your domain) |

## Customising
Theme colours: CSS variables at the top of `app/static/css/main.css`. Everything else
(logo, text, links, works, pricing) is editable in the admin panel.

## Security built in

- Passwords hashed (Werkzeug); login limited to 10 tries / 15 min per IP; sessions are HttpOnly, SameSite=Lax, Secure in production, and "strong" (replayed sessions are logged out)
- CSRF protection on the whole admin panel; every destructive action is POST-only
- Database access only through the SQLAlchemy ORM (no raw SQL → no SQL injection)
- Templates auto-escape all output; user text is also cleaned with `bleach`; links go through a `safe_url` filter that blocks `javascript:` URLs
- Uploads: extension whitelist **and** file-signature check, random filenames, 50 MB cap, content type chosen by the server
- Security headers on every response: CSP, HSTS (production), X-Frame-Options, nosniff, Referrer-Policy, Permissions-Policy; admin pages are never cached
- App refuses to start in production without a strong `SECRET_KEY`; debug mode is off
- Dependencies pinned and scanned (`pip-audit`: no known vulnerabilities at release time). Re-check every few months:
  `pip install pip-audit` then `pip-audit -r requirements.txt`

## Still on you (cannot be automated)

1. Set a strong, unique admin password (`python scripts/set_admin_password.py`, 12+ characters).
2. Turn on 2-factor authentication on GitHub, Render, Neon and Cloudflare.
3. Never commit `.env`; rotate any key you ever pasted somewhere public.
4. Visitor messages contain personal data (name, email, IP) — keep the admin password private and delete old messages you don't need.
