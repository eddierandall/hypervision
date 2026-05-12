# Hyper Vision · Patient Portal

A password-gated landing experience: presents as a sterile medical login portal,
glitches and flatlines after a few seconds, then reveals a subscribe page where
visitors leave an email address.

The entire inner page is encrypted at rest. Only the password unlocks it.

---

## Repo layout

```
.
├── portal.html         # Source: the unencrypted Hyper Vision page (DO NOT publish)
├── encrypt.py          # Build script: portal.html → docs/index.html + docs/gate.css
├── setup.sql           # Supabase schema setup (run once against your project)
├── requirements.txt    # Python dependency for the build script
├── .gitignore
├── README.md           # this file
└── docs/               # Production output — what gets served publicly
    ├── index.html      # Encrypted wrapper with the password gate
    └── gate.css        # Lock-screen styles
```

**Source files at the repo root are never served.** Only `docs/` is published.

---

## Current password

```
G0B!lls
```

Stored only as a key-derivation input in `encrypt.py`. Change it before going
live with anything sensitive (see "Re-encrypting" below).

A successful unlock is remembered for 24 hours via `localStorage` (key
`hv.gate.v1`). Clear that key in DevTools to force a re-prompt.

---

## Deploying with GitHub Pages

1. **Push this repo to GitHub** (private is fine).
2. **Settings → Pages**:
   - Source: **Deploy from a branch**
   - Branch: **main** · Folder: **/docs**
   - Save
3. Within ~1–2 minutes the site is live at `https://<you>.github.io/<repo>/`.

> ⚠️ **Heads up about private repos and GitHub Pages.** On free GitHub plans,
> Pages from a private repo is still served *publicly*. The `/docs` layout
> protects you here: only `docs/index.html` and `docs/gate.css` are reachable,
> and those are the encrypted/safe files. `portal.html` and `encrypt.py` sit
> at the repo root and are never served, no matter your plan.

If you'd rather not use GitHub Pages, the `docs/` folder is a normal static
site and works on Netlify, Vercel, Cloudflare Pages, S3, or any host. Just
point the host at `docs/`.

---

## Editing the source page

1. Edit `portal.html` to change copy, branding, glitch timing, etc.
2. Re-run the build:
   ```bash
   pip install -r requirements.txt   # first time only
   python3 encrypt.py
   ```
3. Commit the regenerated `docs/index.html` and `docs/gate.css`, push, done.

> Each rebuild generates a fresh random salt and IV, so the ciphertext changes
> even when the password and source don't. That's expected.

---

## Re-encrypting with a new password

Two ways:

```bash
# One-off override, leaves DEFAULT_PASSWORD in the script untouched
PORTAL_PASSWORD='your-new-passphrase' python3 encrypt.py
```

Or edit the `DEFAULT_PASSWORD` constant at the top of `encrypt.py` and just run
`python3 encrypt.py`.

A longer passphrase (4+ random words) is dramatically more brute-force
resistant than a short password like the current default. Recommended if the
gate matters.

---

## Email storage — Supabase

Submissions write to a `subscribers` table in your Supabase project. Fields
captured per submitter:

| column | type | notes |
| --- | --- | --- |
| `email` | `TEXT` | primary key, stored lowercased |
| `first_name` | `TEXT` | required |
| `last_name` | `TEXT` | required |
| `birthday` | `TEXT` | required, MM/DD format, CHECK-constrained |
| `unsubscribed` | `CHAR(1)` | `'Y'` or `'N'`, defaults to `'N'` |
| `created_at` | `TIMESTAMPTZ` | defaults to `NOW()` |

### One-time setup

1. **Create a Supabase project** at [supabase.com](https://supabase.com).
2. **Run `setup.sql`** — in the Supabase dashboard, go to SQL Editor, paste
   the contents of `setup.sql` from this repo, and click Run. This creates
   the table, normalizes emails to lowercase via a trigger, enables Row Level
   Security, and adds an INSERT-only policy for anonymous visitors. The script
   is idempotent — safe to re-run.
3. **Wire the frontend** to your project. In `portal.html`, find the two
   constants near the bottom of the script section:
   ```js
   const SUPABASE_URL      = 'https://YOUR-PROJECT.supabase.co';
   const SUPABASE_ANON_KEY = 'YOUR-ANON-KEY';
   ```
   Replace both with values from Supabase → Project Settings → API. The anon
   key is safe to commit — it's intended for the browser, and the RLS policy
   from `setup.sql` is what protects the data.
4. **Re-encrypt and deploy** the updated portal:
   ```bash
   python3 encrypt.py
   git add portal.html docs/index.html
   git commit -m "Wire Supabase"
   git push
   ```

### What anonymous visitors can and can't do

The RLS policy in `setup.sql` allows the `anon` role (used by the browser)
to **insert** rows but does **not** grant `SELECT`, `UPDATE`, or `DELETE`.
That means:

- ✅ Visitors can subscribe.
- ❌ Visitors **cannot** read other people's emails by guessing API calls.
- ❌ Visitors cannot mark anyone as unsubscribed (you'll handle that yourself
  when an unsubscribe link is added later).

### Reading / exporting the list

Two easy paths:

- **Dashboard**: Supabase → Table Editor → `subscribers` → filter / sort / export to CSV.
- **SQL Editor**: e.g.
  ```sql
  SELECT first_name, last_name, email, birthday, created_at
  FROM subscribers
  WHERE unsubscribed = 'N'
  ORDER BY created_at DESC;
  ```

The dashboard uses the `service_role` key, which bypasses RLS, so you see everything.

### Duplicate handling

A repeat submission with an existing email gets a friendly *"You're already on
the list"* message rather than an error. Postgres returns error code `23505`
on the unique-violation, which the form treats as a successful (idempotent)
subscribe.

---

## What "encrypted" actually means here

- The full HTML/CSS/JS of the inner page is encrypted with **AES-256-GCM**.
- The key is derived from the password via **PBKDF2-SHA256** with **500,000
  iterations** and a random 16-byte salt.
- The salt and 12-byte IV are stored in the page (this is standard — they're
  not secrets, only the password is).
- AES-GCM is authenticated, so a wrong password fails cleanly with an
  `InvalidTag` error rather than producing garbage HTML.

What this stops: casual snooping, view-source curiosity, search-engine
indexing, accidentally sharing a link.

What this doesn't stop: a determined attacker willing to spend GPU time
brute-forcing a short password offline. Use a long passphrase if that
threat model applies.
