#!/usr/bin/env python3
"""Build the static guides site for guides.bsrhrb.com from markdown sources in content/."""
import html
import json
import re
import shutil
from pathlib import Path

import markdown

ROOT = Path(__file__).parent
CONTENT = ROOT / "content"
OUT = ROOT / "docs"  # GitHub Pages serves from /docs
SITE = "https://guides.bsrhrb.com"
SCREENER = "https://bsrhrb.com"
AUTHOR = "Alicja Salter"
AUTHOR_ROLE = "Building Surveyor and BSR compliance consultant (MSc Building Surveying)"


def parse(path: Path):
    """Content files: front matter (key: value lines) then '---' then markdown body."""
    text = path.read_text(encoding="utf-8")
    head, body = text.split("\n---\n", 1)
    meta = {}
    for line in head.strip().splitlines():
        k, v = line.split(":", 1)
        meta[k.strip()] = v.strip()
    meta["body"] = body.strip()
    return meta


def autolink(body: str, pages, current_slug: str) -> str:
    """Turn plain mentions of other guide titles into internal links (first mention only)."""
    for p in pages:
        if p["slug"] == current_slug:
            continue
        for t in (p["h1"], p["h1"].split(":")[0]):
            # skip if already inside a markdown link
            pattern = re.compile(r"(?<![\[\w])" + re.escape(t) + r"(?![\w\]])")
            body, n = pattern.subn(f"[{t}](../{p['slug']}/)", body, count=1)
            if n:
                break
    return body


CSS = """
:root{--bg:#fbfaf7;--surface:#ffffff;--ink:#1d2433;--muted:#5a6375;--line:#e4e1d8;--accent:#b4462b;--accent-ink:#ffffff;--soft:#f3efe6;--link:#1f5f8b}
@media (prefers-color-scheme:dark){:root{--bg:#14171d;--surface:#1b1f27;--ink:#e8e6e1;--muted:#a3a9b5;--line:#2d333e;--accent:#e0714f;--accent-ink:#14171d;--soft:#222731;--link:#7fb6dc}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.65 "Source Serif 4",Georgia,"Times New Roman",serif}
a{color:var(--link)}
.wrap{max-width:720px;margin:0 auto;padding:0 16px}
header.site{border-bottom:1px solid var(--line);background:var(--surface)}
header.site .wrap{display:flex;align-items:center;justify-content:space-between;gap:12px;min-height:60px;flex-wrap:wrap;padding-top:8px;padding-bottom:8px}
.brand{font:600 16px/1.2 "Inter",system-ui,sans-serif;color:var(--ink);text-decoration:none;letter-spacing:.01em}
.brand span{color:var(--accent)}
.btn{display:inline-block;font:600 15px/1 "Inter",system-ui,sans-serif;background:var(--accent);color:var(--accent-ink);text-decoration:none;padding:12px 16px;border-radius:6px}
.btn:hover{filter:brightness(1.05)}
nav.crumbs{font:14px/1.4 "Inter",system-ui,sans-serif;color:var(--muted);margin:28px 0 8px}
nav.crumbs a{color:var(--muted)}
h1{font-size:clamp(28px,6vw,40px);line-height:1.15;margin:8px 0 12px;letter-spacing:-.01em}
h2{font-size:24px;line-height:1.25;margin:40px 0 8px}
h3{font-size:20px;line-height:1.3;margin:28px 0 6px}
.lede{font-size:19px;color:var(--muted)}
.byline{font:14px/1.5 "Inter",system-ui,sans-serif;color:var(--muted);border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:10px 0;margin:16px 0 28px}
article table{border-collapse:collapse;width:100%;font:15px/1.45 "Inter",system-ui,sans-serif;margin:16px 0;display:block;overflow-x:auto}
article th,article td{border:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}
article th{background:var(--soft)}
article li{margin:4px 0}
.cta{background:var(--soft);border:1px solid var(--line);border-radius:10px;padding:20px;margin:36px 0}
.cta p{margin:0 0 12px;font:16px/1.5 "Inter",system-ui,sans-serif}
.cta strong{display:block;font-size:18px;margin-bottom:4px}
.note{font:14px/1.55 "Inter",system-ui,sans-serif;color:var(--muted)}
.sources{font-size:15px}
ul.guides{list-style:none;padding:0;margin:24px 0}
ul.guides li{border-top:1px solid var(--line);padding:16px 0}
ul.guides li:last-child{border-bottom:1px solid var(--line)}
ul.guides a{font-size:20px;line-height:1.3;font-weight:600;text-decoration:none;color:var(--ink)}
ul.guides a:hover{color:var(--accent)}
ul.guides p{margin:4px 0 0;color:var(--muted);font:15px/1.5 "Inter",system-ui,sans-serif}
.hero{padding:40px 0 8px}
footer.site{margin-top:56px;border-top:1px solid var(--line);background:var(--surface)}
footer.site .wrap{padding-top:24px;padding-bottom:32px;font:14px/1.6 "Inter",system-ui,sans-serif;color:var(--muted)}
"""

FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap" rel="stylesheet">'


def layout(title, desc, canonical, body, depth, jsonld=None):
    base = "../" * depth
    ld = f'<script type="application/ld+json">{json.dumps(jsonld)}</script>' if jsonld else ""
    return f"""<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="article">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="BSR Guides">
<link rel="icon" href="{base}favicon.svg" type="image/svg+xml">
{FONTS}
<style>{CSS}</style>
{ld}
</head>
<body>
<header class="site"><div class="wrap">
<a class="brand" href="{base or './'}">BSR <span>Guides</span></a>
<a class="btn" href="{SCREENER}">Check your project</a>
</div></header>
<main class="wrap">
{body}
</main>
<footer class="site"><div class="wrap">
<p>Written by {AUTHOR}, {AUTHOR_ROLE}. These guides cover existing higher-risk buildings in England. They are general information, not legal advice or a building control decision. Always confirm with the Building Safety Regulator or a suitably qualified professional before you start work.</p>
<p>We may receive a referral fee from consultants we recommend if you instruct them. This does not change your screening result, and you are free to use any consultant you choose.</p>
<p><a href="{base or './'}">All guides</a> · <a href="{SCREENER}">BSR screener</a></p>
</div></footer>
</body>
</html>
"""


CTA = f"""<div class="cta"><p><strong>Not sure whether your project needs BSR approval?</strong>Answer a few questions about your building and your planned work and get a PDF report on whether Building Safety Regulator approval is likely to be needed.</p><a class="btn" href="{SCREENER}">Start the BSR screener</a></div>"""


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    pages = [parse(p) for p in sorted(CONTENT.glob("*.md"))]
    pages.sort(key=lambda p: int(p.get("order", 99)))
    md = markdown.Markdown(extensions=["tables", "sane_lists"])

    for p in pages:
        body_md = autolink(p["body"], pages, p["slug"])
        # split off a trailing Sources section so it can be styled
        md.reset()
        content_html = md.convert(body_md)
        content_html = content_html.replace("<h2>Sources</h2>", '<h2 id="sources">Sources</h2>')
        canonical = f"{SITE}/{p['slug']}/"
        jsonld = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": p["h1"],
            "description": p["description"],
            "author": {"@type": "Person", "name": AUTHOR, "jobTitle": "Building Surveyor and BSR compliance consultant"},
            "dateModified": p["reviewed"],
            "mainEntityOfPage": canonical,
            "inLanguage": "en-GB",
        }
        body = f"""<nav class="crumbs"><a href="../">BSR Guides</a> › Guide</nav>
<article>
<h1>{html.escape(p['h1'])}</h1>
<div class="byline">By {AUTHOR}, {AUTHOR_ROLE} · Last reviewed {p['reviewed_human']}</div>
{content_html}
{CTA}
</article>"""
        d = OUT / p["slug"]
        d.mkdir(parents=True)
        (d / "index.html").write_text(layout(p["title"], p["description"], canonical, body, 1, jsonld), encoding="utf-8")

    # index
    items = "\n".join(
        f'<li><a href="{p["slug"]}/">{html.escape(p["h1"])}</a><p>{html.escape(p["description"])}</p></li>' for p in pages
    )
    idx_body = f"""<section class="hero">
<h1>Plain-English guides to BSR approval for flat works</h1>
<p class="lede">Refurbishing a flat in a high-rise block in England? If the building is higher-risk, most building work needs approval from the Building Safety Regulator before it starts. These guides explain the rules, the timelines and what to check first.</p>
</section>
{CTA}
<h2>Guides</h2>
<ul class="guides">
{items}
</ul>"""
    site_ld = {"@context": "https://schema.org", "@type": "WebSite", "name": "BSR Guides", "url": SITE + "/"}
    (OUT / "index.html").write_text(
        layout(
            "BSR Approval Guides for Flat Works in High-Rise Buildings",
            "Plain-English guides to Building Safety Regulator approval for flat refurbishments in higher-risk buildings in England, by building surveyor Alicja Salter.",
            SITE + "/",
            idx_body,
            0,
            site_ld,
        ),
        encoding="utf-8",
    )

    # 404
    (OUT / "404.html").write_text(
        layout("Page not found | BSR Guides", "Page not found.", SITE + "/404.html",
               '<h1 style="margin-top:40px">Page not found</h1><p>That page doesn\'t exist. <a href="/">See all guides</a> or <a href="' + SCREENER + '">try the BSR screener</a>.</p>', 0),
        encoding="utf-8",
    )

    # sitemap, robots, CNAME, favicon
    urls = [SITE + "/"] + [f"{SITE}/{p['slug']}/" for p in pages]
    lastmods = {SITE + "/": max(p["reviewed"] for p in pages)}
    lastmods.update({f"{SITE}/{p['slug']}/": p["reviewed"] for p in pages})
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sm += "".join(f"  <url><loc>{u}</loc><lastmod>{lastmods[u]}</lastmod></url>\n" for u in urls)
    sm += "</urlset>\n"
    (OUT / "sitemap.xml").write_text(sm, encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
    (OUT / "CNAME").write_text("guides.bsrhrb.com\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    (OUT / "favicon.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="6" fill="#b4462b"/>'
        '<rect x="9" y="6" width="14" height="20" rx="1.5" fill="none" stroke="#fff" stroke-width="2"/>'
        '<path d="M12 11h3M17 11h3M12 15h3M17 15h3M12 19h3M17 19h3" stroke="#fff" stroke-width="2"/></svg>',
        encoding="utf-8",
    )
    print(f"Built {len(pages)} guides into {OUT}")


if __name__ == "__main__":
    build()
