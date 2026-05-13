# Hyper Vision Patient Portal

A responsive patient registration portal for Hyper Vision.

## Flow

1. **Password gate** — enter the access code to proceed
2. **Light landing page** — auto-transitions after 4 seconds via glitch effect
3. **Dark registration form** — fill in First Name, Last Name, Email and submit
4. **Confirmation page** — thank you screen with the HV brand lockup

## Usage

Everything is contained in a single `index.html` file with all assets embedded as base64 — no build step, no dependencies, no server required.

Just open `index.html` in any modern browser, or deploy to any static host (GitHub Pages, Netlify, Vercel, etc.).

## Deploying to GitHub Pages

1. Push this repo to GitHub
2. Go to **Settings → Pages**
3. Set source to the `main` branch, root folder
4. Your portal will be live at `https://<username>.github.io/<repo-name>/`

## Stack

- Pure HTML5 / CSS3 / Vanilla JS — no frameworks
- Google Fonts (Rajdhani, Orbitron, Share Tech Mono) — loaded from CDN
- All images embedded as base64 — single portable file
