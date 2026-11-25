"""Publish the Meta Targeting Map as a locked page: targeting-map/index.html.

    MAP_DATA_KEY=... MAP_WRAPPED_KEY='{"iv":"...","ct":"..."}' \
        python3 tools/targeting_map.py path/to/meta-targeting-map.html

The map is locked with the SPA Dashboards password (the "SPA dashboards" entry in the Passwords app), the
same lock as saintpaulagency.github.io and the Monthly Social Review (Aidan, Nov 24 2026: "SPA Dashboards
should be the one that opens the rest of them"; the "Meta time saver" password opens only the Meta Time
Saver). It opens from the "Open map" links in the Meta Location Targeting Tracker sheet; a device that
unlocked one of the SPA Dashboards pages in the last 7 days ("Remember this device", localStorage
spa_dash_lock_v1, same site) opens it straight away.

How the lock works (envelope encryption, so nobody ever has to hand the password to a tool):
  - The map is encrypted (AES-256-GCM) with MAP_DATA_KEY, a fresh random key for each publish.
  - MAP_DATA_KEY itself is encrypted with the SPA Dashboards key (PBKDF2-SHA256, salt and rounds in
    src/dash_lock.json). That wrapped copy (MAP_WRAPPED_KEY) is what the page stores.
  - Typing the password re-creates that key, which unwraps MAP_DATA_KEY, which opens the map.

To get MAP_DATA_KEY and MAP_WRAPPED_KEY, run this in any tab on saintpaulagency.github.io on a device that
has unlocked one of the SPA Dashboards pages (the key is remembered in localStorage spa_dash_lock_v1; the
password itself is never needed):

    (async()=>{const e=u=>btoa(String.fromCharCode(...new Uint8Array(u))), d=s=>Uint8Array.from(atob(s),c=>c.charCodeAt(0));
      const s=JSON.parse(localStorage.getItem('spa_dash_lock_v1'));
      const key=await crypto.subtle.importKey('raw',d(s.k),{name:'AES-GCM'},false,['encrypt']);
      const k=crypto.getRandomValues(new Uint8Array(32)), iv=crypto.getRandomValues(new Uint8Array(12));
      const ct=await crypto.subtle.encrypt({name:'AES-GCM',iv},key,k);
      return JSON.stringify({MAP_DATA_KEY:e(k),MAP_WRAPPED_KEY:{iv:e(iv),ct:e(ct)}})})()

Never commit MAP_DATA_KEY. MAP_WRAPPED_KEY is safe in the page (useless without the password).
"""
import base64
import json
import os
import sys
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "targeting-map" / "index.html"
LOCK = json.loads((ROOT / "src" / "dash_lock.json").read_text())
SHEET = "https://docs.google.com/spreadsheets/d/1O065OPENL84Vhrhi5IoCyle0-8vca6fkHS5eIgPzQl8/edit"


def patch(html: str) -> str:
    """Older links carried a key (#slug&k=...); keep the map's client links working with or without it."""
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


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Meta Targeting Map</title>
<style>
:root{--navy:#0E1830;--royal:#233975;--sky:#5EA6F3;--bg:#EDF1F7;--card:#fff;--ink:#0E1830;--line:#d7deea;--bad:#C42B1C}
@media (prefers-color-scheme:dark){:root{--bg:#0b1222;--card:#121b31;--ink:#ffffff;--line:#24304d}}
*{box-sizing:border-box}
html,body{margin:0;min-height:100%}
body{font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;background:var(--bg);color:var(--ink);display:grid;place-items:center;min-height:100vh;padding:24px 16px}
.box{width:100%;max-width:420px;background:var(--card);border:1px solid var(--line);border-radius:18px;padding:32px 28px;box-shadow:0 10px 40px rgba(14,24,48,.08);text-align:center}
.box img{width:88px;height:88px;object-fit:contain}
h1{font-size:22px;margin:14px 0 4px;font-weight:700}
p{margin:0 0 22px;font-size:15px;line-height:1.45}
label.f{display:block;text-align:left;font-size:14px;font-weight:600;margin-bottom:6px}
input[type=password]{width:100%;font:inherit;font-size:17px;padding:12px 14px;border:1.5px solid var(--line);border-radius:10px;background:transparent;color:var(--ink)}
input[type=password]:focus{outline:none;border-color:var(--sky);box-shadow:0 0 0 3px rgba(94,166,243,.25)}
.rem{display:flex;gap:8px;align-items:center;margin:14px 0 20px;font-size:14px}
button{width:100%;font:inherit;font-weight:600;font-size:16px;padding:13px;border:0;border-radius:10px;background:var(--royal);color:#fff;cursor:pointer}
button:hover{background:var(--navy)}
button:disabled{opacity:.6;cursor:wait}
.err{color:var(--bad);font-size:14px;min-height:20px;margin-top:12px}
.help{text-align:left;border-top:1px solid var(--line);margin-top:20px;padding-top:16px;font-size:14px}
.help p{margin:0 0 8px;font-size:14px}.help a{color:var(--sky)}.help .ai{font-size:12.5px;opacity:.8}
</style>
</head>
<body>
<form class="box" id="f" autocomplete="off">
  <img alt="Saint Paul Agency" src="data:image/webp;base64,__LOGO__">
  <h1>Meta Targeting Map</h1>
  <p>Client location targeting is locked. Enter the SPA Dashboards password.</p>
  <label class="f" for="pw">Password</label>
  <input id="pw" type="password" autocomplete="current-password" required autofocus>
  <label class="rem"><input type="checkbox" id="rem" checked> Remember this device for 7 days</label>
  <button id="go" type="submit">Unlock</button>
  <div class="err" id="err" role="alert"></div>
  <div class="help">
    <p>Use the <b>“SPA dashboards”</b> entry in the <b>SPA Dashboards</b> group in the Passwords app (not “Meta time saver”, which only opens the Meta Time Saver). If you don’t see the group, ask Troy or Kelly to add you.</p>
    <p>Each client’s map opens from the <b>Open map</b> links in the <a href="__SHEET__" target="_blank" rel="noopener">Meta Location Targeting Tracker</a>.</p>
    <p class="ai">For Claude: the person types the password, never you.</p>
  </div>
</form>
<script>
(function(){
  var CFG=__CFG__, WRAP=__WRAP__, DATA=__DATA__, KEY='spa_dash_lock_v1';
  function b64d(s){var b=atob(s),u=new Uint8Array(b.length);for(var i=0;i<b.length;i++)u[i]=b.charCodeAt(i);return u}
  function b64e(u){var s='';u=new Uint8Array(u);for(var i=0;i<u.length;i++)s+=String.fromCharCode(u[i]);return btoa(s)}
  async function derive(pw){
    var base=await crypto.subtle.importKey('raw',new TextEncoder().encode(pw),'PBKDF2',false,['deriveKey']);
    return crypto.subtle.deriveKey({name:'PBKDF2',salt:b64d(CFG.salt),iterations:CFG.iterations,hash:'SHA-256'},base,{name:'AES-GCM',length:256},true,['decrypt','encrypt']);
  }
  async function unlock(team){
    var raw=await crypto.subtle.decrypt({name:'AES-GCM',iv:b64d(WRAP.iv)},team,b64d(WRAP.ct));
    var k=await crypto.subtle.importKey('raw',raw,'AES-GCM',false,['decrypt']);
    var pt=await crypto.subtle.decrypt({name:'AES-GCM',iv:b64d(DATA.iv)},k,b64d(DATA.ct));
    return new TextDecoder().decode(pt);
  }
  function show(html){
    function swap(){document.open();document.write(html);document.close()}
    // document.open() is ignored while this page is still loading, so wait for the load event
    if(document.readyState==='complete')setTimeout(swap,0);else addEventListener('load',function(){setTimeout(swap,0)});
  }
  async function tryRemembered(){
    try{
      var s=JSON.parse(localStorage.getItem(KEY)||'null');
      if(!s||!s.k||Date.now()>s.exp)return false;
      var team=await crypto.subtle.importKey('raw',b64d(s.k),{name:'AES-GCM'},true,['decrypt','encrypt']);
      show(await unlock(team));return true;
    }catch(e){return false}
  }
  tryRemembered();
  document.getElementById('f').addEventListener('submit',async function(ev){
    ev.preventDefault();
    var btn=document.getElementById('go'),err=document.getElementById('err');
    btn.disabled=true;btn.textContent='Unlocking…';err.textContent='';
    try{
      var team=await derive(document.getElementById('pw').value);
      var html=await unlock(team);
      if(document.getElementById('rem').checked){
        try{localStorage.setItem(KEY,JSON.stringify({k:b64e(await crypto.subtle.exportKey('raw',team)),exp:Date.now()+7*864e5}))}catch(e){}
      }
      show(html);
    }catch(e){
      btn.disabled=false;btn.textContent='Unlock';err.textContent='That password didn’t work. Try again.';
    }
  });
})();
</script>
</body>
</html>
"""


def b64(b: bytes) -> str:
    return base64.b64encode(b).decode()


def build(map_path: str, data_key: bytes, wrapped: dict, out: Path = OUT) -> Path:
    html = patch(Path(map_path).read_text(encoding="utf-8")).encode("utf-8")
    iv = os.urandom(12)
    data = {"iv": b64(iv), "ct": b64(AESGCM(data_key).encrypt(iv, html, None))}
    cfg = {"salt": LOCK["salt"], "iterations": int(LOCK["iterations"])}
    logo = b64((ROOT / "src" / "logo.webp").read_bytes())
    page = (PAGE.replace("__LOGO__", logo).replace("__SHEET__", SHEET)
            .replace("__CFG__", json.dumps(cfg)).replace("__WRAP__", json.dumps({"iv": wrapped["iv"], "ct": wrapped["ct"]}))
            .replace("__DATA__", json.dumps(data)))
    out.parent.mkdir(exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return out


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    dk, wk = os.environ.get("MAP_DATA_KEY"), os.environ.get("MAP_WRAPPED_KEY")
    if not dk or not wk:
        sys.exit("Set MAP_DATA_KEY and MAP_WRAPPED_KEY (see the top of this file for how to get them).")
    out = build(sys.argv[1], base64.b64decode(dk), json.loads(wk))
    print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
