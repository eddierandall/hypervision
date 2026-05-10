#!/usr/bin/env python3
"""
Encrypts portal.html with AES-256-GCM and writes a password-gated
docs/index.html + docs/gate.css. Decryption happens entirely client-side
via WebCrypto.

Usage:
    python3 encrypt.py                          # uses default password
    PORTAL_PASSWORD='newpass' python3 encrypt.py  # override password

Requires: cryptography  (pip install -r requirements.txt)
"""
import base64, json, os, sys, pathlib
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ---- Configuration ----------------------------------------------------------
DEFAULT_PASSWORD = "G0B!lls"
PASSWORD   = os.environ.get("PORTAL_PASSWORD", DEFAULT_PASSWORD)
ITERATIONS = 500_000

# ---- Paths (relative to this script) ----------------------------------------
HERE = pathlib.Path(__file__).resolve().parent
SRC_HTML = HERE / "portal.html"
DOCS_DIR = HERE / "docs"
OUT_HTML = DOCS_DIR / "index.html"
OUT_CSS  = DOCS_DIR / "gate.css"

if not SRC_HTML.exists():
    sys.exit(f"error: source file not found: {SRC_HTML}")
DOCS_DIR.mkdir(exist_ok=True)

plaintext = SRC_HTML.read_text(encoding="utf-8")

salt = os.urandom(16)
iv   = os.urandom(12)

kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITERATIONS)
key = kdf.derive(PASSWORD.encode("utf-8"))

ct = AESGCM(key).encrypt(iv, plaintext.encode("utf-8"), None)

payload = {
    "v": 1,
    "kdf": "PBKDF2-SHA256",
    "iterations": ITERATIONS,
    "salt": base64.b64encode(salt).decode(),
    "iv":   base64.b64encode(iv).decode(),
    "ct":   base64.b64encode(ct).decode(),
}

GATE_CSS = """\
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { height: 100%; }
body {
  font-family: 'Space Mono', monospace;
  background: #050608;
  color: #c8c2b6;
  display: grid;
  place-items: center;
  overflow: hidden;
  -webkit-font-smoothing: antialiased;
}
body::before {
  content: '';
  position: fixed; inset: 0;
  background: repeating-linear-gradient(
    0deg,
    rgba(255,255,255,0) 0px,
    rgba(255,255,255,0) 2px,
    rgba(255,255,255,0.022) 3px,
    rgba(255,255,255,0) 4px
  );
  pointer-events: none;
  z-index: 1;
}
body::after {
  content: '';
  position: fixed; inset: 0;
  background: radial-gradient(closest-side, transparent 55%, rgba(0,0,0,0.75) 100%);
  pointer-events: none;
  z-index: 1;
}
.gate {
  position: relative;
  z-index: 2;
  width: min(440px, calc(100% - 48px));
  text-align: center;
  opacity: 0;
  transition: opacity 0.4s ease;
}
.gate.ready { opacity: 1; animation: fade-in 0.7s ease backwards 0.1s; }
@keyframes fade-in {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
.lock-mark {
  width: 36px; height: 36px;
  margin: 0 auto 32px;
  border: 1.5px solid rgba(232,225,210,0.55);
  border-radius: 2px;
  position: relative;
}
.lock-mark::before {
  content: '';
  position: absolute;
  width: 18px; height: 12px;
  border: 1.5px solid rgba(232,225,210,0.55);
  border-bottom: none;
  border-radius: 9px 9px 0 0;
  left: 50%; top: -12px;
  transform: translateX(-50%);
}
.lock-mark::after {
  content: '';
  position: absolute;
  width: 4px; height: 8px;
  background: rgba(232,225,210,0.7);
  left: 50%; top: 50%;
  transform: translate(-50%, -50%);
  border-radius: 1px;
}
.eyebrow {
  font-size: 11px;
  letter-spacing: 6px;
  color: #d8324a;
  text-transform: uppercase;
  margin-bottom: 18px;
}
h1 {
  font-family: 'VT323', monospace;
  font-size: 32px;
  font-weight: 400;
  color: #ece5d6;
  letter-spacing: 4px;
  margin-bottom: 12px;
}
.desc {
  font-size: 11px;
  color: rgba(232,225,210,0.5);
  letter-spacing: 1.5px;
  text-transform: uppercase;
  margin-bottom: 36px;
  line-height: 1.7;
}
.form {
  display: flex;
  border: 1px solid rgba(232,225,210,0.18);
  background: rgba(255,255,255,0.02);
  border-radius: 2px;
  transition: border-color 0.18s, box-shadow 0.18s;
}
.form:focus-within {
  border-color: rgba(216,50,74,0.55);
  box-shadow: 0 0 0 3px rgba(216,50,74,0.12);
}
.form.shake { animation: shake 0.4s; }
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20%, 60% { transform: translateX(-8px); }
  40%, 80% { transform: translateX(8px); }
}
input {
  flex: 1;
  padding: 16px 18px;
  background: transparent;
  border: none;
  font-family: 'Space Mono', monospace;
  font-size: 14px;
  color: #ece5d6;
  letter-spacing: 4px;
}
input:focus { outline: none; }
input::placeholder {
  color: rgba(232,225,210,0.3);
  letter-spacing: 2px;
}
button {
  padding: 0 22px;
  background: rgba(216,50,74,0.95);
  color: #fff;
  border: none;
  cursor: pointer;
  font-family: 'Space Mono', monospace;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 3px;
  font-weight: 700;
  transition: background 0.15s;
}
button:hover:not(:disabled) { background: #b41e36; }
button:disabled {
  background: rgba(232,225,210,0.1);
  color: rgba(232,225,210,0.5);
  cursor: wait;
}
.status {
  margin-top: 22px;
  font-size: 11px;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: rgba(232,225,210,0.45);
  min-height: 16px;
}
.status.error { color: #d8324a; }
.status.working { color: rgba(232,225,210,0.7); }
.status.success { color: #2ec4a6; }
.footer-mark {
  margin-top: 64px;
  font-family: 'VT323', monospace;
  font-size: 13px;
  letter-spacing: 4px;
  color: rgba(232,225,210,0.22);
}
.blink { animation: blink 1.1s steps(2, start) infinite; }
@keyframes blink { to { visibility: hidden; } }
"""

WRAPPER = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<meta name="robots" content="noindex, nofollow" />
<title>Restricted</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=VT323&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="gate.css" />
</head>
<body>
<div class="gate">
  <div class="lock-mark" aria-hidden="true"></div>
  <div class="eyebrow">Authorization</div>
  <h1>RESTRICTED</h1>
  <p class="desc">Credential required<br>to proceed</p>
  <form class="form" id="gate-form" autocomplete="off" spellcheck="false">
    <input id="pw" type="password" placeholder="••••••••" required aria-label="Password" />
    <button type="submit" id="go">Enter</button>
  </form>
  <div class="status" id="status">&nbsp;</div>
  <div class="footer-mark">/// AWAITING<span class="blink">_</span></div>
</div>

<script id="payload" type="application/json">__PAYLOAD__</script>
<script>
(function () {
  const payload = JSON.parse(document.getElementById('payload').textContent);
  const gate    = document.querySelector('.gate');
  const form    = document.getElementById('gate-form');
  const pwIn    = document.getElementById('pw');
  const goBtn   = document.getElementById('go');
  const status  = document.getElementById('status');

  // ----- Remember-me settings -----
  // Stored in localStorage (more reliable than document.cookie for static
  // files, and avoids needing Secure/SameSite/path correctness). If you
  // specifically need an HTTP cookie instead, swap the get/set/remove calls
  // below for: document.cookie = `${KEY}=${value}; max-age=86400; path=/`;
  const STORAGE_KEY  = 'hv.gate.v1';
  const REMEMBER_MS  = 24 * 60 * 60 * 1000; // 24 hours

  function loadRemembered() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      const data = JSON.parse(raw);
      if (!data || !data.pw || !data.exp) return null;
      if (Date.now() > data.exp) {
        localStorage.removeItem(STORAGE_KEY);
        return null;
      }
      return data.pw;
    } catch (e) { return null; }
  }
  function saveRemembered(pw) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        pw, exp: Date.now() + REMEMBER_MS
      }));
    } catch (e) { /* private mode etc — silent fail is fine */ }
  }
  function clearRemembered() {
    try { localStorage.removeItem(STORAGE_KEY); } catch (e) {}
  }

  // ----- Crypto helpers -----
  function b64ToBytes(b64) {
    const bin = atob(b64);
    const out = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }
  async function deriveKey(password, salt, iterations) {
    const enc = new TextEncoder();
    const baseKey = await crypto.subtle.importKey(
      'raw', enc.encode(password), { name: 'PBKDF2' }, false, ['deriveKey']
    );
    return crypto.subtle.deriveKey(
      { name: 'PBKDF2', salt, iterations, hash: 'SHA-256' },
      baseKey,
      { name: 'AES-GCM', length: 256 },
      false,
      ['decrypt']
    );
  }
  async function tryUnlock(password) {
    const salt = b64ToBytes(payload.salt);
    const iv   = b64ToBytes(payload.iv);
    const ct   = b64ToBytes(payload.ct);
    const key  = await deriveKey(password, salt, payload.iterations);
    const ptBuf = await crypto.subtle.decrypt({ name: 'AES-GCM', iv }, key, ct);
    return new TextDecoder().decode(ptBuf);
  }

  // ----- UI handlers -----
  function reveal(html) {
    document.open();
    document.write(html);
    document.close();
  }
  function fail(msg) {
    status.textContent = '> ' + msg;
    status.className = 'status error';
    form.classList.remove('shake'); void form.offsetWidth; form.classList.add('shake');
    goBtn.disabled = false;
    pwIn.disabled = false;
    pwIn.value = '';
    pwIn.focus();
  }
  function showGate() {
    gate.classList.add('ready');
    setTimeout(() => pwIn.focus(), 150);
  }

  form.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const pw = pwIn.value;
    if (!pw) { fail('credential required'); return; }

    goBtn.disabled = true;
    pwIn.disabled  = true;
    status.className = 'status working';
    status.textContent = '> verifying…';

    try {
      const html = await tryUnlock(pw);
      saveRemembered(pw);
      status.className = 'status success';
      status.textContent = '> access granted · 24h';
      await new Promise(r => setTimeout(r, 280));
      reveal(html);
    } catch (e) {
      fail('access denied');
    }
  });

  // ----- Auto-unlock on load -----
  (async function init() {
    const remembered = loadRemembered();
    if (!remembered) { showGate(); return; }

    // Try silent unlock. Keep gate hidden so there's no flash.
    try {
      const html = await tryUnlock(remembered);
      reveal(html);
    } catch (e) {
      // Stored credential no longer works (page was re-encrypted, etc.)
      clearRemembered();
      showGate();
    }
  })();
})();
</script>
</body>
</html>
"""

out = WRAPPER.replace("__PAYLOAD__", json.dumps(payload))

OUT_HTML.write_text(out, encoding="utf-8")
OUT_CSS.write_text(GATE_CSS, encoding="utf-8")

print(f"✓ {OUT_HTML.relative_to(HERE)}  ({len(out):,} bytes)")
print(f"✓ {OUT_CSS.relative_to(HERE)}   ({len(GATE_CSS):,} bytes)")
print(f"  password: {'(env override)' if 'PORTAL_PASSWORD' in os.environ else 'default'}")
print(f"  PBKDF2 iterations: {ITERATIONS:,}")
