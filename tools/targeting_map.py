"""Publish the Meta Targeting Map as a locked page: targeting-map/index.html.

    MAP_KEY=... python3 tools/targeting_map.py path/to/meta-targeting-map.html

The map is encrypted (AES-256-GCM) with MAP_KEY, a random key that lives only in the
"Open map" links of the Meta Location Targeting Tracker sheet (the part after "k=").
Anyone who opens the map from the sheet gets straight in; without the key the page only
shows a note pointing to the sheet, and the repo holds nothing readable.

Run without MAP_KEY to make a new key. Then put it in the two Map formulas of the sheet
('By client'!F2 and 'By campaign'!F2). Never commit the key.
"""
import base64
import json
import os
import secrets
import sys
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "targeting-map" / "index.html"
SHEET = "https://docs.google.com/spreadsheets/d/1O065OPENL84Vhrhi5IoCyle0-8vca6fkHS5eIgPzQl8/edit"


def b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def unb64u(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def patch(html: str) -> str:
    """Keep the key in the link when the map changes client (#slug&k=KEY)."""
    swaps = [
        ("history.replaceState(null,'','#'+slug)",
         "history.replaceState(null,'','#'+slug+(window.__spaK?'&k='+window.__spaK:''))"),
        ("location.hash=slug}",
         "location.hash=slug+(window.__spaK?'&k='+window.__spaK:'')}"),
        ("h=(location.hash||'').slice(1)",
         "h=(location.hash||'').slice(1).split('&').filter(p=>p.indexOf('k=')!==0)[0]||''"),
    ]
    for old, new in swaps:
        if html.count(old) != 1:
            sys.exit(f"map changed: expected one copy of {old!r}")
        html = html.replace(old, new)
    return html.replace("<head>", '<head><meta name="robots" content="noindex, nofollow">', 1)


LOADER = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Meta Targeting Map</title>
<style>
body{margin:0;min-height:100vh;display:grid;place-items:center;background:#f4f3ef;color:#1b1b19;font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:460px;padding:24px}
h1{font-size:20px;margin:0 0 8px}
a{color:#1c5cab;font-weight:600}
</style>
</head>
<body>
<main id="msg"><p>Opening the map…</p></main>
<script>
(function () {
  var DATA = __DATA__;
  var SHEET = "__SHEET__";
  function fail() {
    document.getElementById('msg').innerHTML = '<h1>Open this map from the tracker sheet</h1>' +
      '<p>The Meta Targeting Map opens from the <b>Open map</b> links in the ' +
      '<a href="' + SHEET + '">Meta Location Targeting Tracker</a>. This link is missing its key.</p>';
  }
  function bytes(s, url) {
    if (url) { s = s.replace(/-/g, '+').replace(/_/g, '/'); while (s.length % 4) s += '='; }
    var b = atob(s), a = new Uint8Array(b.length);
    for (var i = 0; i < b.length; i++) a[i] = b.charCodeAt(i);
    return a;
  }
  var kp = location.hash.slice(1).split('&').filter(function (p) { return p.indexOf('k=') === 0; })[0];
  if (!kp || !window.crypto || !crypto.subtle) return fail();
  var k = kp.slice(2);
  crypto.subtle.importKey('raw', bytes(k, true), 'AES-GCM', false, ['decrypt'])
    .then(function (key) { return crypto.subtle.decrypt({ name: 'AES-GCM', iv: bytes(DATA.iv) }, key, bytes(DATA.ct)); })
    .then(function (pt) {
      window.__spaK = k;
      var html = new TextDecoder().decode(pt);
      function swap() { document.open(); document.write(html); document.close(); }
      // document.open() is ignored while this page is still loading, so wait for the load event
      if (document.readyState === 'complete') setTimeout(swap, 0); else addEventListener('load', function () { setTimeout(swap, 0); });
    })
    .catch(fail);
})();
</script>
</body>
</html>
"""


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    html = patch(Path(sys.argv[1]).read_text(encoding="utf-8"))
    key_s = os.environ.get("MAP_KEY")
    if not key_s:
        key_s = b64u(secrets.token_bytes(32))
        print("new key (put it in the sheet's Map links, never in the repo):", key_s)
    key = unb64u(key_s)
    iv = os.urandom(12)
    ct = AESGCM(key).encrypt(iv, html.encode("utf-8"), None)
    data = json.dumps({"iv": base64.b64encode(iv).decode(), "ct": base64.b64encode(ct).decode()})
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(LOADER.replace("__DATA__", data).replace("__SHEET__", SHEET), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
