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

## ⚠️ Email storage in production

The subscribe form currently saves emails via `window.storage`, which only
exists inside Anthropic's artifact runtime. **Once deployed to GitHub Pages /
Netlify / etc., that API does not exist** — emails will silently not be saved.

In `portal.html`, find the block marked:

```js
// ----- ARTIFACT STORAGE (swap for your backend in production) -----
```

Replace it with one of:

- **Formspree** — `<form action="https://formspree.io/f/YOUR-ID" method="POST">`,
  no backend required. Free tier covers 50 submissions/month.
- **Buttondown / ConvertKit / Mailchimp** — use their HTML form embed; emails
  go straight into a real mailing list you can send from.
- **Your own backend** — a simple `fetch('https://api.yoursite.com/subscribe',
  { method: 'POST', body: JSON.stringify({ email }) })` call.
- **Supabase / Firebase** — if you want a real database without writing a
  server.

After editing `portal.html`, re-run `python3 encrypt.py` to regenerate the
encrypted output.

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
