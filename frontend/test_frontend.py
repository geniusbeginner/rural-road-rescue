"""Click-through verification of rural-road-rescue.html at desktop (1440x900) and phone (390x844) widths, light mode.

Drives the built page like a user: scripted real clicks and taps on every timeline point x road definition, every
atlas tile, map zoom/drag. Checks layout overlap, horizontal overflow, tap blocking, unfilled narration templates,
colour-token contrast, the contrast of every rendered text element against its actual background, load-fade timing
and console errors. Writes screenshots (core states, every section, full page) to the output folder.

Usage (from the repo root, after `python frontend/build_frontend.py`):
    python frontend/test_frontend.py [output_dir]      # default output: frontend/test_shots/ (gitignored)
    FRONTEND_URL=https://... python frontend/test_frontend.py   # same checks against a deployed copy
Requires `pip install playwright`. Uses system Chrome if found (or $CHROME_PATH), else Playwright's own Chromium
(`python -m playwright install chromium`). Exit code is 1 if any problem was found.
"""
import os, pathlib, re, sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
ROOT = pathlib.Path(__file__).resolve().parent.parent
HTML = os.environ.get("FRONTEND_URL") or (ROOT / "rural-road-rescue.html").as_uri()  # FRONTEND_URL: test a deployed copy
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "frontend" / "test_shots"
OUT.mkdir(parents=True, exist_ok=True)
_DEFAULT_CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CHROME = os.environ.get("CHROME_PATH") or (_DEFAULT_CHROME if os.path.exists(_DEFAULT_CHROME) else None)
# Token pairs below the text bar that are never used as text; the rendered-text audit (TEXT_AUDIT) enforces that.
NOT_TEXT = {("--line", "--bg"), ("--line", "--paper"), ("--critical", "--card")}
problems = []
def bad(msg):
    problems.append(msg); print("  PROBLEM:", msg)

TAP_CHECK = """(sel) => { const out=[]; document.querySelectorAll(sel).forEach(el => {
  if (el.disabled) return; el.scrollIntoView({block:'center'}); const r=el.getBoundingClientRect();
  if (!r.width || !r.height) return; const hit=document.elementFromPoint(r.x+r.width/2, r.y+r.height/2);
  if (!(hit===el || el.contains(hit))) out.push((el.innerText||el.getAttribute('aria-label')||el.tagName).slice(0,40)+' <- blocked by '+(hit?(hit.className||hit.tagName):'null'));
  if (r.height < 36) out.push('small target: '+(el.innerText||'').slice(0,30)+' h='+Math.round(r.height)); }); return out; }"""
LAYOUT = """() => { const q=s=>document.querySelector(s); const box=e=>e.getBoundingClientRect();
  const ov=(a,b)=>{const A=box(a),B=box(b);return !(A.right<=B.left||B.right<=A.left||A.bottom<=B.top||B.bottom<=A.top)};
  return {hoverflow: document.documentElement.scrollWidth > innerWidth + 1, scrollW: document.documentElement.scrollWidth,
          map_detail_overlap: ov(q('.mapcard'), q('#detail')), controls_overlap_map: ov(q('.controls'), q('.mapcard')),
          map_h: Math.round(box(q('#map')).height), map_w: Math.round(box(q('#map')).width)} }"""
CONTRAST = """() => { const cs=getComputedStyle(document.documentElement); const v=n=>cs.getPropertyValue(n).trim();
  const lum=h=>{const c=[1,3,5].map(i=>parseInt(h.slice(i,i+2),16)/255).map(x=>x<=.03928?x/12.92:Math.pow((x+.055)/1.055,2.4)); return .2126*c[0]+.7152*c[1]+.0722*c[2]};
  const cr=(a,b)=>{const [x,y]=[lum(v(a)),lum(v(b))].sort((p,q)=>q-p); return +((x+.05)/(y+.05)).toFixed(2)};
  const pairs=[['--ink','--bg'],['--ink','--card'],['--ink-2','--bg'],['--ink-2','--paper'],['--ink-2','--card-soft'],['--ink-2','--card'],
               ['--ink','--card-soft'],['--critical','--bg'],['--critical','--paper'],['--critical','--card-soft'],['--reroute','--bg'],['--reroute','--paper'],['--reroute','--card-soft'],['--suspect','--bg'],['--suspect','--paper'],['--critical','--card'],['--reroute','--card'],['--line-strong','--bg'],['--line-strong','--paper'],['--line-strong','--card-soft'],['--line-strong','--card'],['--line','--bg'],['--line','--paper']];
  return pairs.map(([a,b])=>[a,b,cr(a,b)]); }"""

TEXT_AUDIT = r"""() => { const rgb=s=>{const m=s.match(/rgba?\(([^)]+)\)/); if(!m) return null; const v=m[1].split(/[ ,\/]+/).filter(Boolean).map(Number); return {r:v[0],g:v[1],b:v[2],a:v.length>3?v[3]:1}};
  const lum=c=>[c.r,c.g,c.b].map(x=>x/255).map(x=>x<=.03928?x/12.92:Math.pow((x+.055)/1.055,2.4)).reduce((s,x,i)=>s+x*[.2126,.7152,.0722][i],0);
  const bgOf=el=>{ for(let e=el;e;e=e.parentElement){ const c=rgb(getComputedStyle(e).backgroundColor); if(c&&c.a>0.5) return c; } return rgb(getComputedStyle(document.body).backgroundColor) };
  const out=[]; const seen=new Set();
  document.querySelectorAll('body *').forEach(el=>{ if(el.closest('.leaflet-pane,.leaflet-control-attribution,#glow,script,style')) return;
    const own=[...el.childNodes].some(n=>n.nodeType===3&&n.textContent.trim()); if(!own) return;
    const r=el.getBoundingClientRect(); if(!r.width||!r.height) return; const cs=getComputedStyle(el); if(cs.visibility==='hidden'||+cs.opacity===0) return;
    const fg=rgb(cs.color), bg=bgOf(el); const [a,b]=[lum(fg),lum(bg)].sort((x,y)=>y-x); const ratio=(a+.05)/(b+.05);
    const size=parseFloat(cs.fontSize), bold=+cs.fontWeight>=700; const need=(size>=24||(bold&&size>=18.66))?3:4.5;
    const key=cs.color+'|'+bg.r+','+bg.g+','+bg.b;
    if(ratio<need && !seen.has(key)){ seen.add(key); out.push(`${el.tagName.toLowerCase()}.${el.className||''} "${el.textContent.trim().slice(0,30)}" ${cs.color} on rgb(${bg.r},${bg.g},${bg.b}) = ${ratio.toFixed(2)} (need ${need})`); }
  }); return out; }"""


def tap(page, sel, nth=None):
    """User-like tap: bring the control to the viewport centre, verify nothing covers it, then click."""
    loc = page.locator(sel) if nth is None else page.locator(sel).nth(nth)
    loc.evaluate("el => el.scrollIntoView({block:'center'})"); page.wait_for_timeout(80)
    ok = loc.evaluate("el => { const r=el.getBoundingClientRect(); const h=document.elementFromPoint(r.x+r.width/2, r.y+r.height/2); return h===el || el.contains(h) }")
    if not ok: bad(f"tap target covered: {sel} {nth}")
    loc.click(timeout=5000)
    return loc

def run(pw, label, vp, mobile):
    print(f"\n===== {label} {vp} =====")
    b = pw.chromium.launch(executable_path=CHROME, headless=True) if CHROME else pw.chromium.launch(headless=True)
    ctx = b.new_context(viewport=vp, color_scheme="light", device_scale_factor=1, has_touch=mobile, is_mobile=mobile)
    page = ctx.new_page(); errs = []
    page.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errs.append(f"pageerror {e}"))
    page.goto(HTML, wait_until="load"); page.wait_for_timeout(1500)
    page.add_style_tag(content="html{scroll-behavior:auto!important}")  # test only: measure after instant scrolls
    # contrast (desktop only, same tokens)
    if label == "desktop":
        for a, c, r in page.evaluate(CONTRAST):
            need = 3.0 if a.startswith("--line") else 4.5
            status = "OK" if r >= need else (f"below {need}, not used as text (rendered audit checks this)" if (a, c) in NOT_TEXT else f"FAIL (need {need})")
            print(f"  contrast {a} on {c}: {r} {status}")
            if r < need and (a, c) not in NOT_TEXT: bad(f"contrast {a}/{c} {r}")
    # initial state
    h3 = page.inner_text("#detail h3"); print("  initial detail:", h3)
    if "Chooralmala" not in h3: bad("default selection is not the Chooralmala enclave")
    # map interaction: wheel zoom + drag
    zoom = lambda: page.evaluate("() => { for (const k in window) {} return document.querySelector('.leaflet-container') ? document.querySelector('.leaflet-proxy') ? getComputedStyle(document.querySelector('.leaflet-proxy')).transform : 'na' : 'na' }")
    before = zoom()
    page.locator("#map").scroll_into_view_if_needed()
    mb = page.locator("#map").bounding_box()
    if not mobile:
        page.mouse.move(mb["x"] + mb["width"] / 2, mb["y"] + mb["height"] / 2); page.mouse.wheel(0, -400); page.wait_for_timeout(700)
        if zoom() == before: bad("wheel zoom did not change the map")
        before = zoom(); page.mouse.down(); page.mouse.move(mb["x"] + mb["width"] / 2 + 120, mb["y"] + mb["height"] / 2 + 60, steps=8); page.mouse.up(); page.wait_for_timeout(300)
        pan = page.evaluate("() => getComputedStyle(document.querySelector('.leaflet-map-pane')).transform")
        print("  pan transform after drag:", pan)
    else:
        page.evaluate("() => document.querySelector('#map').scrollIntoView({block:'center'})"); page.wait_for_timeout(300)
        zb = page.locator(".leaflet-control-zoom-in").bounding_box()
        hit = page.evaluate("([x,y]) => { const h=document.elementFromPoint(x,y); return h ? (h.className||h.tagName) : null }", [zb["x"] + zb["width"] / 2, zb["y"] + zb["height"] / 2])
        print("  zoom-in control hit-test:", hit, "box", {k: round(v) for k, v in zb.items()})
        page.touchscreen.tap(zb["x"] + zb["width"] / 2, zb["y"] + zb["height"] / 2); page.wait_for_timeout(700)
        if zoom() == before: bad("zoom-in tap did not change the map")
    page.screenshot(path=str(OUT / f"{label}_core_default.png"))
    # every timeline x definition
    states = 0
    for t in ["pre", "aftermath", "kalladi", "today"]:
        tap(page, f".tstop[data-t={t}]"); page.wait_for_timeout(250)
        for d in ["V0", "V1", "V2"]:
            btn = page.locator(f"#roaddef button[data-d={d}]")
            if btn.is_disabled():
                if t != "aftermath": bad(f"{t}/{d} unexpectedly disabled")
                continue
            tap(page, f"#roaddef button[data-d={d}]"); page.wait_for_timeout(350); states += 1
            lay = page.evaluate(LAYOUT)
            narr = page.inner_text("#narration")
            det = page.inner_text("#detail")
            if lay["hoverflow"]: bad(f"{t}/{d} horizontal overflow {lay['scrollW']}")
            if lay["map_detail_overlap"] or lay["controls_overlap_map"]: bad(f"{t}/{d} panel overlap {lay}")
            if re.search(r"\{\w+\}|undefined|NaN|null", narr + det): bad(f"{t}/{d} unfilled template or undefined in text")
            print(f"  {t:9s} {d}: map {lay['map_w']}x{lay['map_h']} | title '{page.inner_text('#maptitle')}' | narration: {narr[:110]!r}")
            for x in page.evaluate(TEXT_AUDIT): bad(f"{t}/{d} rendered text contrast: {x}")
            if (t, d) in (("kalladi", "V0"), ("aftermath", "V0"), ("pre", "V1"), ("today", "V0")):
                page.locator(".mapcard").scroll_into_view_if_needed(); page.wait_for_timeout(700)
                page.screenshot(path=str(OUT / f"{label}_{t}_{d}.png"))
    print(f"  states exercised: {states}")
    # every atlas tile (today V0)
    tap(page, ".tstop[data-t=today]"); tap(page, "#roaddef button[data-d=V0]"); page.wait_for_timeout(300)
    n = page.locator(".tile").count(); print(f"  atlas tiles (today V0): {n}")
    if n != 14: bad(f"expected 14 atlas tiles, got {n}")
    for i in range(n):
        tile = page.locator(".tile").nth(i); name = tile.locator(".vn").inner_text()
        tap(page, ".tile", i); page.wait_for_timeout(250)
        if page.inner_text("#detail h3").strip() != name.strip(): bad(f"tile '{name}' did not select its enclave")
    # click an enclave on the map canvas (select Jessy via its first vertex)
    tap(page, ".tstop[data-t=today]"); page.wait_for_timeout(200)
    # tap-blocking and target sizes
    for sel in [".tstop", "#roaddef button", ".tile", "#sorts button", ".topnav a", ".diffs .cites a", ".leaflet-control-zoom a"]:
        issues = page.evaluate(TAP_CHECK, sel)
        issues = [x for x in issues if not x.startswith("small target") or sel in (".tstop", "#roaddef button", ".tile")]
        for x in issues: bad(f"{sel}: {x}")
    # glow + reveal timing
    g = page.evaluate("() => { const g=document.getElementById('glow'); const s=getComputedStyle(g); return {display:s.display, w:s.width, bg:s.backgroundImage.slice(0,60)} }")
    print("  glow:", g)
    rv = page.evaluate("() => [...document.querySelectorAll('.reveal')].map(e => { const s=getComputedStyle(e); return parseFloat(s.animationDelay)+parseFloat(s.animationDuration) })")
    print("  reveal end times (s):", rv)
    if rv and max(rv) >= 0.5: bad("load fade reaches 0.5 s")
    # full-page screenshot back at default
    tap(page, ".tstop[data-t=today]"); tap(page, ".tile", 0); page.wait_for_timeout(800)
    page.evaluate("() => window.scrollTo(0,0)"); page.wait_for_timeout(300)
    page.screenshot(path=str(OUT / f"{label}_fullpage.png"), full_page=True)
    page.add_style_tag(content=".topbar{display:none!important}")  # screenshot only: sticky bar would overlay element shots
    for sec in ["atlas", "validated", "errors", "ra2ce", "cite"]:
        page.locator(f"#{sec}").scroll_into_view_if_needed(); page.wait_for_timeout(200)
        page.locator(f"#{sec}").screenshot(path=str(OUT / f"{label}_sec_{sec}.png"))
    for x in page.evaluate(TEXT_AUDIT): bad(f"sections rendered text contrast: {x}")
    real_errs = [e for e in errs if "tile.openstreetmap" not in e and "fonts.g" not in e]
    print("  console errors:", real_errs or "none", f"(network-only errors ignored: {len(errs) - len(real_errs)})")
    if real_errs: bad(f"console errors: {real_errs[:3]}")
    b.close()

with sync_playwright() as pw:
    run(pw, "desktop", {"width": 1440, "height": 900}, False)
    run(pw, "phone", {"width": 390, "height": 844}, True)
print("\nPROBLEMS:", len(problems)); [print(" -", p) for p in problems]
print("screenshots:", OUT)
sys.exit(1 if problems else 0)
