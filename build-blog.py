#!/usr/bin/env python3
"""
build-blog.py — Hard Work & Pain blog page generator

WHAT THIS DOES
Reads blog-posts.json (one entry per post) and regenerates, from scratch,
every time you run it:
  1. blog/<slug>/index.html   — a real, standalone, crawlable page per post
  2. sitemap.xml              — updated with every post's URL
  3. index.html               — the blog card grid AND the in-app `posts`
                                 JS array are replaced (everything else in
                                 index.html is left untouched)

HOW TO ADD A NEW POST
  1. Open blog-posts.json
  2. Copy one of the existing {...} entries, paste it as a new item in the
     array (position in the array = display order on the site)
  3. Fill in: slug, tag, title, date, read, description, excerpt, body
       - slug: lowercase-with-dashes, must be unique, becomes the URL
               (hardworkandpain.com/blog/<slug>/)
       - tag: category label shown on the card (e.g. "Training")
       - title: full post title
       - date: e.g. "August 2026"
       - read: e.g. "5 min read"
       - description: ~1-2 sentence meta description (for Google, not shown
                       on the page itself)
       - excerpt: the ~2 sentence blurb shown on the blog listing card
       - body: the post HTML, same as the others (use <p>, <h2>, <ul>,
               <div class="callout">...</div>, etc.) — write it as a normal
               Python triple-quoted string, not a JS template literal
  4. Run:  python3 build-blog.py
  5. Commit + push (or paste the changed files into GitHub's web editor):
       - index.html
       - sitemap.xml
       - the new blog/<slug>/index.html file

REQUIREMENTS
  Just Python 3, no packages to install. Run from the repo root (the same
  folder that contains index.html, sitemap.xml, and blog-posts.json).
"""

import json
import os
import re
import sys
from datetime import date

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
POSTS_JSON = os.path.join(REPO_ROOT, "blog-posts.json")
INDEX_HTML = os.path.join(REPO_ROOT, "index.html")
SITEMAP_XML = os.path.join(REPO_ROOT, "sitemap.xml")
BLOG_DIR = os.path.join(REPO_ROOT, "blog")
SITE_URL = "https://hardworkandpain.com"

REQUIRED_FIELDS = ["slug", "tag", "title", "date", "read", "description", "excerpt", "body"]

MONTH_MAP = {
    'January': '01', 'February': '02', 'March': '03', 'April': '04',
    'May': '05', 'June': '06', 'July': '07', 'August': '08',
    'September': '09', 'October': '10', 'November': '11', 'December': '12',
}


def load_posts():
    if not os.path.exists(POSTS_JSON):
        sys.exit(f"ERROR: {POSTS_JSON} not found. Run this script from the repo root.")
    with open(POSTS_JSON, encoding="utf-8") as f:
        posts = json.load(f)
    if not isinstance(posts, list) or not posts:
        sys.exit("ERROR: blog-posts.json must be a non-empty JSON array.")
    slugs_seen = set()
    for i, post in enumerate(posts):
        missing = [k for k in REQUIRED_FIELDS if k not in post or not str(post[k]).strip()]
        if missing:
            sys.exit(f"ERROR: post #{i} ({post.get('title', '?')}) is missing: {', '.join(missing)}")
        if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', post["slug"]):
            sys.exit(f"ERROR: post #{i} has an invalid slug '{post['slug']}' — use lowercase letters, numbers, and dashes only.")
        if post["slug"] in slugs_seen:
            sys.exit(f"ERROR: duplicate slug '{post['slug']}' — slugs must be unique.")
        slugs_seen.add(post["slug"])
    return posts


def to_iso(date_str):
    parts = date_str.split(' ')
    if len(parts) == 2 and parts[0] in MONTH_MAP:
        return f"{parts[1]}-{MONTH_MAP[parts[0]]}-01"
    return date.today().isoformat()


def json_escape(s):
    return s.replace('\\', '\\\\').replace('"', '\\"')


def js_template_escape(s):
    # Escape characters that would break a JS template literal
    return s.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')


POST_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />

<!-- ══ PRIMARY SEO ══ -->
<title>{title} | Hard Work & Pain</title>
<meta name="description" content="{description}" />
<meta name="keywords" content="{tag}, fitness, workout tracker, Hard Work And Pain, Platemate" />
<meta name="author" content="Hard Work & Pain" />
<link rel="canonical" href="{canonical}" />

<!-- ══ OPEN GRAPH ══ -->
<meta property="og:site_name" content="Hard Work & Pain" />
<meta property="og:type" content="article" />
<meta property="og:url" content="{canonical}" />
<meta property="og:title" content="{title} | Hard Work & Pain" />
<meta property="og:description" content="{description}" />
<meta property="og:image" content="{site_url}/og-image.jpg" />

<!-- ══ TWITTER / X CARD ══ -->
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{title} | Hard Work & Pain" />
<meta name="twitter:description" content="{description}" />
<meta name="twitter:image" content="{site_url}/og-image.jpg" />

<!-- ══ STRUCTURED DATA ══ -->
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{title_json}",
  "description": "{description_json}",
  "author": {{ "@type": "Organization", "name": "Hard Work & Pain" }},
  "publisher": {{ "@type": "Organization", "name": "Hard Work & Pain", "logo": {{ "@type": "ImageObject", "url": "{site_url}/og-image.jpg" }} }},
  "mainEntityOfPage": {{ "@type": "WebPage", "@id": "{canonical}" }},
  "datePublished": "{iso_date}",
  "articleSection": "{tag}"
}}
</script>

<link rel="icon" type="image/x-icon" href="/favicon.ico" />
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />

<!-- ══ GOOGLE ANALYTICS ══ -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-TEKMG83C6G"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-TEKMG83C6G');
</script>

<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
<style>
  :root {{
    --gold: #FFB612;
    --gold-dim: #cc9200;
    --black: #0a0a0a;
    --dark: #111111;
    --card: #161616;
    --border: #2a2a2a;
    --muted: #888;
    --white: #f0f0f0;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html {{ scroll-behavior: smooth; }}
  body {{ background: var(--black); color: var(--white); font-family: 'Inter', sans-serif; font-size: 16px; line-height: 1.6; }}

  nav {{
    position: fixed; top: 0; left: 0; right: 0; z-index: 100;
    background: rgba(10,10,10,0.95); backdrop-filter: blur(10px);
    border-bottom: 1px solid var(--border);
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 40px; height: 64px;
  }}
  .nav-logo {{ font-family: 'Bebas Neue', sans-serif; font-size: 26px; color: var(--gold); letter-spacing: 2px; text-decoration: none; }}
  .nav-logo span {{ color: var(--white); }}
  .nav-links {{ display: flex; gap: 32px; list-style: none; }}
  .nav-links a {{ color: var(--muted); text-decoration: none; font-size: 13px; font-weight: 500; letter-spacing: 0.5px; text-transform: uppercase; transition: color 0.2s; }}
  .nav-links a:hover {{ color: var(--gold); }}
  .nav-cta {{ background: var(--gold); color: #000; border: none; padding: 9px 20px; font-size: 13px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; cursor: pointer; text-decoration: none; transition: background 0.2s; }}
  .nav-cta:hover {{ background: var(--gold-dim); }}

  main {{ padding-top: 64px; }}

  .post-wrap {{ max-width: 760px; margin: 0 auto; padding: 80px 40px; }}
  .post-back {{ display: inline-flex; align-items: center; gap: 8px; color: var(--gold); font-size: 11px; font-weight: 700; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 48px; text-decoration: none; transition: opacity 0.2s; }}
  .post-back:hover {{ opacity: 0.7; }}
  .post-tag {{ font-size: 10px; font-weight: 700; letter-spacing: 3px; text-transform: uppercase; color: var(--gold); margin-bottom: 20px; }}
  .post-title {{ font-family: 'Bebas Neue', sans-serif; font-size: clamp(40px, 7vw, 72px); letter-spacing: 2px; line-height: 1; margin-bottom: 24px; color: var(--white); }}
  .post-meta {{ font-size: 12px; color: var(--muted); letter-spacing: 1px; display: flex; gap: 20px; border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); padding: 16px 0; margin-bottom: 52px; }}
  .post-body {{ color: #ccc; font-size: 16px; line-height: 1.9; }}
  .post-body h2 {{ font-family: 'Bebas Neue', sans-serif; font-size: 32px; letter-spacing: 1px; color: var(--white); margin: 48px 0 16px; }}
  .post-body h2 span {{ color: var(--gold); }}
  .post-body p {{ margin-bottom: 24px; }}
  .post-body strong {{ color: var(--white); font-weight: 600; }}
  .post-body .callout {{ background: var(--card); border-left: 3px solid var(--gold); padding: 20px 24px; margin: 32px 0; font-size: 15px; color: var(--muted); }}
  .post-body ul {{ margin: 0 0 24px 0; padding-left: 0; list-style: none; }}
  .post-body ul li {{ padding: 8px 0 8px 20px; position: relative; border-bottom: 1px solid var(--border); font-size: 15px; }}
  .post-body ul li::before {{ content: '→'; position: absolute; left: 0; color: var(--gold); }}

  .post-nav {{ margin-top: 72px; padding-top: 40px; border-top: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; }}
  .post-nav-btn {{ background: var(--card); border: 1px solid var(--border); color: var(--white); padding: 12px 20px; font-size: 12px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; text-decoration: none; transition: border-color 0.2s, color 0.2s; }}
  .post-nav-btn:hover {{ border-color: var(--gold); color: var(--gold); }}

  footer {{ border-top: 1px solid var(--border); padding: 28px 40px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 20px; }}
  .footer-logo {{ font-family: 'Bebas Neue', sans-serif; font-size: 22px; color: var(--gold); letter-spacing: 2px; }}
  .footer-logo span {{ color: var(--white); }}
  .footer-copy {{ color: var(--muted); font-size: 12px; }}
  .footer-links {{ display: flex; gap: 24px; }}
  .footer-links a {{ color: var(--muted); text-decoration: none; font-size: 12px; letter-spacing: 1px; text-transform: uppercase; transition: color 0.2s; }}
  .footer-links a:hover {{ color: var(--gold); }}

  @media (max-width: 768px) {{
    nav {{ padding: 0 20px; }}
    .nav-links {{ display: none; }}
    .post-wrap {{ padding: 60px 20px 40px; }}
    footer {{ flex-direction: column; align-items: flex-start; padding: 28px 20px; }}
  }}
</style>
</head>
<body>

<nav>
  <a href="{site_url}/" class="nav-logo">HARD WORK <span>&amp; PAIN</span></a>
  <ul class="nav-links">
    <li><a href="{site_url}/">Home</a></li>
    <li><a href="{site_url}/#about">About</a></li>
    <li><a href="{site_url}/#blog">Blog</a></li>
    <li><a href="{site_url}/platemate">Platemate</a></li>
    <li><a href="{site_url}/#contact">Contact</a></li>
  </ul>
  <a href="{site_url}/platemate" class="nav-cta">Get the App</a>
</nav>

<main>
<div class="post-wrap">
  <a class="post-back" href="{site_url}/#blog">← Back to Blog</a>
  <div class="post-tag">{tag}</div>
  <h1 class="post-title">{title}</h1>
  <div class="post-meta">
    <span>{date}</span>
    <span>{read}</span>
  </div>
  <div class="post-body">
{body}
  </div>
  <div class="post-nav">
    <a class="post-nav-btn" href="{prev_link}">← {prev_label}</a>
    <a class="post-nav-btn" href="{site_url}/#blog">All Posts</a>
    <a class="post-nav-btn" href="{next_link}">{next_label} →</a>
  </div>
</div>
</main>

<footer>
  <div class="footer-logo">HARD WORK <span>&amp; PAIN</span></div>
  <div class="footer-copy">© {year} Hard Work & Pain. All rights reserved.</div>
  <div class="footer-links">
    <a href="{site_url}/">Home</a>
    <a href="{site_url}/#blog">Blog</a>
    <a href="{site_url}/platemate">Platemate</a>
    <a href="{site_url}/#contact">Contact</a>
  </div>
</footer>

</body>
</html>
"""


def build_post_pages(posts):
    urls = [f"{SITE_URL}/blog/{p['slug']}/" for p in posts]
    written = []
    for i, post in enumerate(posts):
        prev_idx, next_idx = i - 1, i + 1
        if prev_idx >= 0:
            prev_link = urls[prev_idx]
            prev_label = posts[prev_idx]['title'][:28] + ('…' if len(posts[prev_idx]['title']) > 28 else '')
        else:
            prev_link, prev_label = f"{SITE_URL}/#blog", "All Posts"
        if next_idx < len(posts):
            next_link = urls[next_idx]
            next_label = posts[next_idx]['title'][:28] + ('…' if len(posts[next_idx]['title']) > 28 else '')
        else:
            next_link, next_label = f"{SITE_URL}/#blog", "All Posts"

        html = POST_PAGE_TEMPLATE.format(
            title=post['title'],
            title_json=json_escape(post['title']),
            description=post['description'],
            description_json=json_escape(post['description']),
            canonical=urls[i],
            tag=post['tag'],
            iso_date=to_iso(post['date']),
            date=post['date'],
            read=post['read'],
            body=post['body'],
            prev_link=prev_link,
            prev_label=prev_label,
            next_link=next_link,
            next_label=next_label,
            site_url=SITE_URL,
            year=date.today().year,
        )
        post_dir = os.path.join(BLOG_DIR, post['slug'])
        os.makedirs(post_dir, exist_ok=True)
        out_path = os.path.join(post_dir, "index.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        written.append(out_path)
    return written, urls


def build_sitemap(posts, urls):
    today = date.today().isoformat()
    entries = [
        (f"{SITE_URL}/", today, "weekly", "1.0"),
        (f"{SITE_URL}/platemate/", today, "monthly", "0.9"),
    ]
    for url in urls:
        entries.append((url, today, "monthly", "0.8"))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">', '']
    for loc, lastmod, changefreq, priority in entries:
        lines += [
            '  <url>',
            f'    <loc>{loc}</loc>',
            f'    <lastmod>{lastmod}</lastmod>',
            f'    <changefreq>{changefreq}</changefreq>',
            f'    <priority>{priority}</priority>',
            '  </url>', '',
        ]
    lines.append('</urlset>')
    with open(SITEMAP_XML, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def build_blog_cards_html(posts):
    cards = []
    for i, post in enumerate(posts):
        url = f"{SITE_URL}/blog/{post['slug']}/"
        cards.append(
            f'    <a class="blog-card" href="{url}" onclick="showPost({i}); return false;">\n'
            f'      <div class="blog-tag">{post["tag"]}</div>\n'
            f'      <div class="blog-title">{post["title"]}</div>\n'
            f'      <div class="blog-excerpt">{post["excerpt"]}</div>\n'
            f'      <div class="blog-meta"><span>{post["date"]}</span><span>{post["read"]}</span></div>\n'
            f'    </a>'
        )
    return "\n".join(cards)


def build_posts_js_array(posts):
    items = []
    for post in posts:
        body_js = js_template_escape(post['body'])
        title_js = post['title'].replace("\\", "\\\\").replace("'", "\\'")
        items.append(
            "    {\n"
            f"      tag: '{post['tag']}',\n"
            f"      title: '{title_js}',\n"
            f"      date: '{post['date']}',\n"
            f"      read: '{post['read']}',\n"
            f"      body: `\n{body_js}\n      `\n"
            "    }"
        )
    return "const posts = [\n" + ",\n".join(items) + "\n  ];"


def update_index_html(posts):
    with open(INDEX_HTML, encoding="utf-8") as f:
        content = f.read()

    cards_html = build_blog_cards_html(posts)
    cards_pattern = re.compile(
        r'(<!-- BLOG_CARDS_START.*?-->\n)(.*?)(\n\s*<!-- BLOG_CARDS_END -->)',
        re.S
    )
    if not cards_pattern.search(content):
        sys.exit("ERROR: BLOG_CARDS_START/END markers not found in index.html — "
                 "did you edit around them by hand?")
    content = cards_pattern.sub(lambda m: m.group(1) + cards_html + m.group(3), content, count=1)

    posts_js = build_posts_js_array(posts)
    posts_pattern = re.compile(
        r'(// POSTS_ARRAY_START.*?\n)\s*const posts = \[.*?\n  \];(\n  // POSTS_ARRAY_END)',
        re.S
    )
    if not posts_pattern.search(content):
        sys.exit("ERROR: POSTS_ARRAY_START/END markers not found in index.html — "
                 "did you edit around them by hand?")
    content = posts_pattern.sub(lambda m: m.group(1) + "  " + posts_js + m.group(2), content, count=1)

    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    posts = load_posts()
    written, urls = build_post_pages(posts)
    build_sitemap(posts, urls)
    update_index_html(posts)

    print(f"Built {len(posts)} post(s):")
    for p, u in zip(posts, urls):
        print(f"  - {p['title']}  ->  {u}")
    print()
    print("Updated files (commit/push or paste into GitHub):")
    print("  - index.html")
    print("  - sitemap.xml")
    for w in written:
        print(f"  - {os.path.relpath(w, REPO_ROOT)}")


if __name__ == "__main__":
    main()
