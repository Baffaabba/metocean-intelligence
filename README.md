# MetOcean Intelligence Platform

Transfer-learning time series forecasting (FastAPI backend + static frontend),
gated behind email invitation. This is a **private, invite-only** site — there
is no open signup; every account is created by an admin sending an invite.

## Access model

- Admins (hardcoded in `app/src/auth.py:ADMIN_EMAILS`) send invites via
  `POST /admin/invite` or the `/admin.html` panel.
- The invitee gets an email with a one-time link
  (`/accept-invite.html?token=...`) that expires **7 days** after issue.
- Accepting the invite sets their password and creates the account.
- There is no `/auth/signup` route — the only way in is an admin invite.
- Admins can deactivate an account (`DELETE /admin/users/{id}`); a
  deactivated user's `is_active` flag is cleared and they can no longer log
  in or use an existing token.

## Local setup

```bash
cp .env.example .env
# fill in .env — see comments in the file for what each var does
uv sync --group test          # installs everything except heavy ML deps
# torch must be installed separately (CPU or CUDA build), see pyproject.toml
uv run uvicorn app.api:app --reload --port 8000
```

Every variable read by the code is documented in `.env.example`. In
particular:

- `METOCEAN_JWT_SECRET` is **required** — the app refuses to start without
  it (generate with `openssl rand -hex 32`). There is no insecure default.
- `CORS_ORIGINS` must list the real origin(s) the frontend is served from.
  Never set it to `*` in production.
- `ENABLE_API_DOCS` gates Swagger UI (`/docs`) and `/openapi.json`. Leave it
  `false` in production so the full API surface (admin/invite routes) isn't
  publicly browsable.

## Email (invitations & password resets)

`EMAIL_PROVIDER` selects the backend:

- `smtp` (default) — any SMTP relay via `SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/
  `SMTP_PASSWORD`. Currently wired to **Brevo's free tier** (300 emails/day,
  no credit card):
  1. Sign up at [brevo.com](https://www.brevo.com).
  2. **Settings → SMTP & API → SMTP tab** — copy the SMTP login and
     generate an SMTP key (this is not your account password).
  3. **Senders, Domains & Dedicated IPs → Senders** — verify the address
     you put in `SENDER_EMAIL` (or verify the whole domain via DNS/DKIM if
     you control `metoceanai.com`'s DNS). Brevo will reject or spam-box
     mail from an unverified sender — this step is not optional.
  4. Set `SMTP_HOST=smtp-relay.brevo.com`, `SMTP_PORT=587`, `SMTP_USER`
     and `SMTP_PASSWORD` from step 2, `SENDER_EMAIL` from step 3.
- `ses` — legacy AWS SES path (`AWS_REGION`/`AWS_ACCESS_KEY_ID`/
  `AWS_SECRET_ACCESS_KEY`). SES starts in sandbox mode (can only send to
  pre-verified addresses) until you request production access from AWS.

If email sending fails, invite/reset creation still succeeds (the token is
valid either way) — check server logs, and the admin panel can resend an
invite once the SMTP config is fixed.

## Deployment

Target: a single Ubuntu EC2 instance running nginx (TLS + reverse proxy) in
front of uvicorn, managed by systemd, with Postgres on the same box.

- **First-time VM setup**: `sudo bash deploy.sh` from a checkout on the VM.
  Installs system packages, PostgreSQL, nginx, the Python env, generates
  `.env` secrets, and registers the systemd unit. Read the "still needed"
  list it prints at the end (TLS cert, email credentials) before treating
  the site as live.
- **Ongoing deploys**: push to `main` — `.github/workflows/deploy-ec2.yml`
  syncs `app/`, `pyproject.toml`, and `uv.lock` to the VM, runs `uv sync`,
  and restarts the service automatically. `redeploy.sh` does the same thing
  manually (for emergencies / working off CI), and is the only script you
  should reach for besides `deploy.sh` — the others were retired as
  duplicates.
- **Required GitHub secrets** (Settings → Secrets and variables → Actions):
  `SSH_PRIVATE_KEY` (the VM's private key), `VM_IP`, `VM_USER`. Consider
  turning on branch protection requiring the `Tests & Coverage` workflow to
  pass before merging to `main`, since a push to `main` deploys straight to
  production.
- `nginx.conf` and `metocean.service` are the tracked reference configs;
  `deploy.sh` installs them as-is to `/etc/nginx/sites-available/metocean`
  and `/etc/systemd/system/metocean.service`. Both assume the VM layout
  `/srv/metocean/app/app/{api.py,src,...}` + `/srv/metocean/app/{pyproject.toml,uv.lock,.env}`
  — i.e. `/srv/metocean/app` mirrors this repo's root exactly, which is
  what `api.py`'s `from app.src.x import ...` imports require.

## Security notes

- Secrets live only in `.env` (gitignored) or GitHub Actions secrets —
  never commit them. If you ever see `.env` or `*.pem` show up in
  `git status`, stop and rotate before doing anything else.
- Rate limiting (`slowapi`) is in-memory and per-process, which is correct
  for the current single-VM deployment. If this ever runs as multiple
  instances behind a load balancer, switch to a shared (e.g. Redis) backend
  or the limits become per-instance instead of global.
- Schema changes (`is_active` on `users`, `expires_at` on `user_invites`)
  are applied via SQLAlchemy `create_all`, which only creates missing
  tables — it does not alter existing ones. On an already-deployed
  database, add the new columns manually before deploying this version:
  ```sql
  ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT true;
  ALTER TABLE user_invites ADD COLUMN expires_at TIMESTAMPTZ;
  UPDATE user_invites SET expires_at = created_at + interval '7 days' WHERE expires_at IS NULL;
  ALTER TABLE user_invites ALTER COLUMN expires_at SET NOT NULL;
  ```

## Tests

```bash
uv run pytest app/tests/ -v                          # everything
uv run pytest app/tests/ -v -m unit                   # fast, no external deps
uv run pytest app/tests/ -v -m "not email"             # what CI runs (email tests need real SMTP)
uv run pytest app/tests/ --cov=app.src --cov-report=html
```

Markers (see `pytest.ini`): `unit`, `integration`, `auth`, `email`, `api`,
`forecast`. CI (`.github/workflows/tests.yml`) runs the suite on Python
3.10 and 3.11, enforces a coverage floor, and runs `trufflehog` on every
push to catch committed secrets before they repeat the `.env`/`.pem`
incident this repo already had once.
