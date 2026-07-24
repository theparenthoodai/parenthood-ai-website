#!/usr/bin/env python3
"""Regenerates the blog and guides sections from markdown sources.

- content/blog/*.md   -> blog/index.html   + blog/<slug>.html
- content/guides/*.md -> guides/index.html + guides/<slug>.html

Run after editing content, then commit the regenerated HTML. Netlify serves
plain static files, no build step there.
"""
import re
import datetime
from pathlib import Path
from html import escape

ROOT = Path(__file__).parent
BLOG_SRC = ROOT / "content" / "blog"
BLOG_OUT = ROOT / "blog"
GUIDES_SRC = ROOT / "content" / "guides"
GUIDES_OUT = ROOT / "guides"
PROOF_DIR = ROOT / "assets" / "img" / "guides"


# ----------------------------- shared chrome -----------------------------

def render_nav(root, active):
    """Site nav. `active` is 'blog' or 'guides' (that link is highlighted and,
    for a page inside that section's folder, points at the local index)."""
    def link(href, label, is_active):
        style = ' style="color:var(--terracotta-500)"' if is_active else ""
        return f'<a class="navlink" href="{href}"{style}>{label}</a>'
    guides_href = "index.html" if active == "guides" else f"{root}guides/"
    blog_href = "index.html" if active == "blog" else f"{root}blog/"
    return f"""  <div class="site-nav">
    <a href="{root}index.html" style="display:flex;align-items:center;gap:10px">
      <img class="nav-logo" src="{root}assets/img/logo-mark.png" alt="Parenthood.ai" style="height:40px;width:auto">
      <span class="serif brand-word" style="font-size:22px;font-weight:600;color:var(--charcoal-900);letter-spacing:.01em">parenthood<span style="color:var(--terracotta-500)">.ai</span></span>
    </a>
    <div class="nav-links" style="display:flex;align-items:center;gap:30px">
      {link(guides_href, "Free guides", active == "guides")}
      {link(blog_href, "Blog", active == "blog")}
      <a class="navlink" href="{root}about.html">About</a>
    </div>
  </div>"""


def render_footer(root):
    return f"""  <div class="site-footer">
    <div class="footer-inner">
      <div class="footer-cols">
        <div>
          <span class="serif" style="font-size:24px;font-weight:600;color:var(--cream-100)">parenthood<span style="color:var(--terracotta-400)">.ai</span></span>
          <p style="margin:12px 0 0;font-size:13px;line-height:1.6;color:rgba(241,236,233,.6);max-width:260px">Simplifying life with help from AI. One simple win at a time.</p>
        </div>
        <div class="footer-col"><span class="wm" style="color:var(--sand-400);margin-bottom:4px">EXPLORE</span><a href="{root}guides/" style="color:inherit">Free guides</a><a href="{root}blog/" style="color:inherit">Blog</a><a href="{root}about.html" style="color:inherit">About</a></div>
        <div class="footer-col"><span class="wm" style="color:var(--sand-400);margin-bottom:4px">FOLLOW</span><a href="https://www.instagram.com/parenthood.ai/" target="_blank" rel="noopener" style="color:inherit">Instagram</a></div>
      </div>
      <div class="footer-bottom">
        <span>© 2026 Parenthood.AI</span>
        <span class="mono" style="letter-spacing:.1em">#SIMPLIFYINGPARENTHOOD</span>
      </div>
    </div>
  </div>"""


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{page_title}</title>
<meta name="description" content="{page_description}">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/img/favicon-32.png">
<link rel="icon" type="image/png" sizes="64x64" href="/assets/img/favicon.png">
<link rel="apple-touch-icon" href="/assets/img/apple-touch-icon.png">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="Parenthood.ai">
<meta property="og:title" content="{page_title}">
<meta property="og:description" content="{page_description}">
<meta property="og:url" content="{og_url}">
<meta property="og:image" content="https://theparenthoodai.com/assets/img/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://theparenthoodai.com/assets/img/og-image.png">
<link rel="stylesheet" href="{root}assets/css/fonts.css">
<link rel="stylesheet" href="{root}assets/css/colors.css">
<link rel="stylesheet" href="{root}assets/css/typography.css">
<link rel="stylesheet" href="{root}assets/css/spacing.css">
<link rel="stylesheet" href="{root}assets/css/effects.css">
<link rel="stylesheet" href="{root}assets/css/base.css">
<link rel="stylesheet" href="{root}assets/css/site.css">
</head>
<body>
<div style="background:var(--cream-200);min-height:100vh;display:flex;flex-direction:column">
{nav}
{content}
{footer}
</div>
</body>
</html>
"""


def slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def parse_frontmatter(text: str):
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not match:
        raise ValueError("missing frontmatter")
    frontmatter, body = match.groups()
    meta = {}
    for line in frontmatter.splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip().strip('"')
    return meta, body


# -------------------------------- blog ----------------------------------

ARTICLE_CONTENT = """  <div class="post-article" style="padding:64px 24px 96px;flex:1">
    <div style="max-width:680px;margin:0 auto">
      <h1 class="serif post-h1" style="margin:0 0 12px;font-weight:600;font-size:46px;line-height:1.12;color:var(--charcoal-900)">{title}</h1>
      <div class="mono" style="font-size:11px;letter-spacing:.1em;color:var(--sand-400);margin-bottom:40px">{date}</div>
      <div class="post-body">
{body_html}
      </div>
      <a href="index.html" style="display:inline-block;margin-top:20px;font-size:14px;font-weight:600;color:var(--terracotta-500)">← Back to Blog</a>
    </div>
  </div>"""

INDEX_CONTENT = """  <div class="blog-header" style="padding:72px 60px 48px;text-align:center">
    <div class="script" style="font-size:32px;color:var(--terracotta-500);margin-bottom:4px">from the journal</div>
    <h1 class="serif blog-h1" style="margin:0;font-weight:600;font-size:52px;color:var(--charcoal-900)">The Blog</h1>
    <p style="margin:16px auto 0;max-width:520px;font-size:15px;line-height:1.6;color:var(--charcoal-500)">Honest writing about learning AI as a parent, one step at a time.</p>
  </div>

  <div class="blog-list" style="padding:8px 60px 100px;flex:1">
    <div style="max-width:820px;margin:0 auto;display:flex;flex-direction:column;gap:24px">
{cards}
    </div>
  </div>"""

CARD = """      <a href="{slug}.html" class="lift" style="display:block;background:var(--surface-card);border:1px solid var(--border-subtle);border-radius:16px;padding:32px 34px;color:inherit">
        <div class="mono" style="font-size:11px;letter-spacing:.1em;color:var(--sand-400);margin-bottom:10px">{date_upper}</div>
        <h2 class="serif" style="margin:0 0 10px;font-weight:600;font-size:28px;line-height:1.15;color:var(--charcoal-900)">{title}</h2>
        <p style="margin:0 0 16px;font-size:14.5px;line-height:1.6;color:var(--charcoal-500)">{excerpt}</p>
        <span style="font-size:13px;font-weight:600;color:var(--terracotta-500)">Read →</span>
      </a>"""


def parse_post(path: Path) -> dict:
    meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))

    # Body is light markdown: blank-line-separated blocks. A block starting with
    # "## " (or "# ") is a section subheading; everything else is a paragraph.
    blocks = [b.strip() for b in body.strip().split("\n\n") if b.strip()]
    parts = []
    first_para = ""
    for b in blocks:
        if b.startswith("## ") or b.startswith("# "):
            heading = b.lstrip("#").strip()
            parts.append(
                '        <h2 class="serif" style="margin:38px 0 12px;font-weight:600;'
                'font-size:27px;line-height:1.25;color:var(--charcoal-900)">'
                f"{escape(heading)}</h2>"
            )
        else:
            para = " ".join(line.strip() for line in b.splitlines())
            parts.append(f"        <p>{escape(para)}</p>")
            if not first_para:
                first_para = para
    body_html = "\n".join(parts)
    excerpt = first_para if len(first_para) <= 160 else first_para[:157].rsplit(" ", 1)[0] + "..."

    # `date` is an ISO date (YYYY-MM-DD) used only to order posts newest-first.
    # Readers see the friendly "Month Year" form. Posts are never numbered.
    raw_date = meta["date"]
    try:
        parsed = datetime.date.fromisoformat(raw_date)
        display_date = parsed.strftime("%B %Y")
        sort_key = parsed.isoformat()
    except ValueError:
        display_date = raw_date
        sort_key = raw_date

    return {
        "title": meta["title"],
        "date": display_date,
        "sort_key": sort_key,
        "slug": slugify(meta["title"]),
        "body_html": body_html,
        "excerpt": excerpt,
    }


def build_blog():
    posts = [parse_post(p) for p in BLOG_SRC.glob("*.md")]
    posts.sort(key=lambda p: p["sort_key"], reverse=True)
    BLOG_OUT.mkdir(exist_ok=True)

    for post in posts:
        content = ARTICLE_CONTENT.format(
            title=escape(post["title"]),
            date="PUBLISHED · " + escape(post["date"]).upper(),
            body_html=post["body_html"],
        )
        page = PAGE.format(
            page_title=f"{post['title']} | Parenthood.ai",
            page_description=escape(post["excerpt"]),
            og_type="article",
            og_url=f"https://theparenthoodai.com/blog/{post['slug']}.html",
            root="../",
            nav=render_nav("../", active="blog"),
            content=content,
            footer=render_footer("../"),
        )
        (BLOG_OUT / f"{post['slug']}.html").write_text(page, encoding="utf-8")
        print(f"wrote {(BLOG_OUT / (post['slug'] + '.html')).relative_to(ROOT)}")

    cards = "\n".join(
        CARD.format(
            slug=post["slug"],
            date_upper="PUBLISHED · " + escape(post["date"]).upper(),
            title=escape(post["title"]),
            excerpt=escape(post["excerpt"]),
        )
        for post in posts
    )
    index_page = PAGE.format(
        page_title="The Blog | Parenthood.ai",
        page_description="Honest writing about learning AI as a parent, one step at a time.",
        og_type="website",
        og_url="https://theparenthoodai.com/blog/",
        root="../",
        nav=render_nav("../", active="blog"),
        content=INDEX_CONTENT.format(cards=cards),
        footer=render_footer("../"),
    )
    (BLOG_OUT / "index.html").write_text(index_page, encoding="utf-8")
    print(f"wrote {(BLOG_OUT / 'index.html').relative_to(ROOT)}")


# -------------------------------- guides --------------------------------

def parse_guide(path: Path) -> dict:
    meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    slug = meta.get("slug") or slugify(meta["title"])

    # Body: intro paragraph(s), then a "## What's inside" heading, then "- " bullets.
    intro_paras, bullets, cur = [], [], []
    for raw in body.strip().splitlines():
        s = raw.strip()
        if s.startswith("- "):
            if cur:
                intro_paras.append(" ".join(cur)); cur = []
            bullets.append(s[2:].strip())
        elif s.startswith("#"):
            if cur:
                intro_paras.append(" ".join(cur)); cur = []
        elif s == "":
            if cur:
                intro_paras.append(" ".join(cur)); cur = []
        else:
            cur.append(s)
    if cur:
        intro_paras.append(" ".join(cur))

    return {
        "title": meta["title"],
        "slug": slug,
        "eyebrow": meta.get("eyebrow", "GUIDE"),
        "card_label": meta.get("card_label", meta["title"]),
        "book_title": meta.get("book_title", meta.get("card_label", meta["title"])),
        "card_desc": meta.get("card_desc", intro_paras[0] if intro_paras else ""),
        "accent": meta.get("accent", "var(--dustytan-500)"),
        "pdf": meta.get("pdf", ""),
        "download_name": meta.get("download_name", ""),
        "meta": meta.get("meta", ""),
        "proof": meta.get("proof") or f"{slug}-example.png",
        "sample_output": meta.get("sample_output", ""),
        "sample_output_name": meta.get("sample_output_name", ""),
        "featured": meta.get("featured", "").lower() == "true",
        "order": int(meta.get("order", "99")),
        "intro_paras": intro_paras,
        "bullets": bullets,
    }


def checklist(bullets):
    return "\n".join(
        '        <div style="display:flex;gap:10px;align-items:flex-start;font-size:14px;'
        'line-height:1.5;color:var(--charcoal-700);margin-bottom:10px">'
        '<span style="color:var(--terracotta-500);font-weight:700">✓</span> '
        f"{escape(b)}</div>"
        for b in bullets
    )


def guide_page_content(g, root):
    intro_html = "\n".join(
        f'      <p style="margin:0 0 16px;font-size:16px;line-height:1.7;color:var(--charcoal-500)">{escape(p)}</p>'
        for p in g["intro_paras"]
    )
    meta_span = (
        f'<span class="mono" style="font-size:11px;color:var(--sand-400)">{escape(g["meta"])}</span>'
        if g["meta"] else ""
    )
    dl = f'{root}public/guides/{g["pdf"]}'

    if (PROOF_DIR / g["proof"]).exists():
        proof_html = (
            f'<img src="{root}assets/img/guides/{g["proof"]}" alt="Example of what the {escape(g["title"])} produces" '
            'style="width:100%;height:auto;border-radius:14px;border:1px solid var(--border-subtle);'
            'box-shadow:var(--shadow-lg);display:block">'
        )
    else:
        proof_html = (
            '<div style="width:100%;aspect-ratio:16/10;border-radius:14px;border:1px dashed var(--border-default);'
            'background:var(--cream-100);display:flex;align-items:center;justify-content:center">'
            '<span class="mono" style="font-size:11px;letter-spacing:.14em;color:var(--sand-400)">EXAMPLE IMAGE COMING SOON</span></div>'
        )

    sample_html = ""
    if g["sample_output"]:
        sample_html = (
            f'\n      <div style="margin-top:14px;text-align:center">'
            f'<a href="{root}public/guides/{g["sample_output"]}" download="{g["sample_output_name"]}" '
            'style="font-size:13px;font-weight:600;color:var(--terracotta-500)">Download the full sample output (PDF) →</a></div>'
        )

    return f"""  <div class="post-article" style="padding:52px 24px 90px;flex:1">
    <div style="max-width:760px;margin:0 auto">
      <a href="index.html" style="display:inline-block;margin-bottom:22px;font-size:13px;font-weight:600;color:var(--terracotta-500)">← All guides</a>
      <div class="mono" style="font-size:11px;letter-spacing:.16em;color:var(--terracotta-500);margin-bottom:8px">{escape(g["eyebrow"])} · FREE</div>
      <h1 class="serif post-h1" style="margin:0 0 14px;font-weight:600;font-size:44px;line-height:1.1;color:var(--charcoal-900)">{escape(g["title"])}</h1>
{intro_html}
      <div class="guide-cta" style="margin-top:22px">
        <a class="pill p-dark" href="{dl}" download="{g["download_name"]}" style="padding:13px 26px;font-size:14px">Download free PDF</a>
        {meta_span}
      </div>

      <h2 class="serif" style="margin:44px 0 16px;font-weight:600;font-size:26px;color:var(--charcoal-900)">What's inside</h2>
{checklist(g["bullets"])}

      <h2 class="serif" style="margin:44px 0 14px;font-weight:600;font-size:26px;color:var(--charcoal-900)">The example build</h2>
      <p style="margin:0 0 18px;font-size:15px;line-height:1.6;color:var(--charcoal-500)">Here's the kind of thing it makes, so you know exactly what you're getting before you start.</p>
      {proof_html}{sample_html}

      <div style="margin:48px 0 8px;text-align:center">
        <a class="pill p-accent" href="{dl}" download="{g["download_name"]}" style="padding:14px 30px;font-size:14px">Download the guide</a>
      </div>
      <div style="text-align:center"><a href="index.html" style="display:inline-block;margin-top:14px;font-size:13px;font-weight:600;color:var(--terracotta-500)">← Back to all guides</a></div>
    </div>
  </div>"""


def guide_card(g):
    return f"""      <a href="{g['slug']}.html" class="lift" style="display:block;background:var(--surface-card);border:1px solid var(--border-subtle);border-radius:14px;overflow:hidden;color:inherit">
        <div style="height:150px;background:{g['accent']};display:flex;align-items:flex-end;padding:16px"><div class="serif" style="color:var(--cream-100);font-size:22px;font-weight:600;font-style:italic">{escape(g['card_label'])}</div></div>
        <div style="padding:20px">
          <span class="mono" style="font-size:10px;letter-spacing:.1em;color:var(--sand-400)">{escape(g['eyebrow'])}</span>
          <h3 class="serif" style="margin:8px 0 6px;font-size:22px;font-weight:600;color:var(--charcoal-900)">{escape(g['title'])}</h3>
          <p style="margin:0 0 16px;font-size:13px;line-height:1.55;color:var(--charcoal-500)">{escape(g['card_desc'])}</p>
          <span style="font-size:13px;font-weight:600;color:var(--terracotta-500)">Read the guide →</span>
        </div>
      </a>"""


def featured_card(g):
    return f"""  <div class="sec-featured" style="padding:8px 60px 44px">
    <a class="featured-card" href="{g['slug']}.html" style="display:grid;grid-template-columns:1.15fr .85fr;gap:48px;align-items:center;background:var(--cream-100);border:1px solid var(--border-subtle);border-radius:20px;padding:44px 46px;max-width:1280px;margin:0 auto;color:inherit">
      <div>
        <span class="pill" style="background:var(--surface-accent);color:var(--charcoal-900);padding:5px 13px;font-size:10px;letter-spacing:.14em;text-transform:uppercase">★ Featured · Free guide</span>
        <h2 class="serif" style="margin:16px 0 0;font-weight:600;font-size:38px;line-height:1.1;color:var(--charcoal-900)">{escape(g['title'])}</h2>
        <p style="margin:14px 0 0;font-size:15px;line-height:1.6;color:var(--charcoal-500);max-width:460px">{escape(g['card_desc'])}</p>
        <div style="margin:22px 0 24px">
{checklist(g['bullets'][:3])}
        </div>
        <span style="font-size:14px;font-weight:600;color:var(--terracotta-500)">Read the guide →</span>
      </div>
      <div class="lift guide-book" style="justify-self:center;width:270px;height:338px;border-radius:12px;background:var(--ink-900);box-shadow:var(--shadow-lg);padding:26px 24px;box-sizing:border-box;display:flex;flex-direction:column;position:relative;overflow:hidden">
        <div class="wm" style="align-self:flex-end;color:rgba(241,236,233,.5);font-size:9px">PARENTHOOD.AI</div>
        <div style="margin-top:auto">
          <div class="mono" style="font-size:9px;letter-spacing:.14em;color:var(--terracotta-400);margin-bottom:12px">{escape(g['eyebrow'])} · FREE</div>
          <div class="serif" style="font-size:27px;line-height:1.08;color:var(--cream-100);font-weight:600">{escape(g['book_title'])}</div>
        </div>
      </div>
    </a>
  </div>"""


def guides_index_content(featured, grid):
    feat = featured_card(featured) if featured else ""
    cards = "\n".join(guide_card(g) for g in grid)
    return f"""  <div class="blog-header" style="padding:72px 60px 40px;text-align:center">
    <div class="script" style="font-size:32px;color:var(--terracotta-500);margin-bottom:2px">always free</div>
    <h1 class="serif blog-h1" style="margin:0;font-weight:600;font-size:52px;color:var(--charcoal-900)">Guides &amp; prompt packs</h1>
    <p style="margin:16px auto 0;max-width:520px;font-size:15px;line-height:1.6;color:var(--charcoal-500)">Short, practical guides that turn AI into real help for your family. No jargon, no fluff.</p>
  </div>
{feat}
  <div class="sec-guides" style="padding:0 60px 84px">
    <div style="max-width:1280px;margin:0 auto">
      <div class="guides-grid" style="display:grid;grid-template-columns:repeat(3,1fr);gap:24px">
{cards}
      </div>
    </div>
  </div>"""


def build_guides():
    guides = [parse_guide(p) for p in GUIDES_SRC.glob("*.md")]
    guides.sort(key=lambda g: g["order"])
    GUIDES_OUT.mkdir(exist_ok=True)

    for g in guides:
        page = PAGE.format(
            page_title=f"{g['title']} | Parenthood.ai",
            page_description=escape(g["card_desc"])[:180],
            og_type="article",
            og_url=f"https://theparenthoodai.com/guides/{g['slug']}.html",
            root="../",
            nav=render_nav("../", active="guides"),
            content=guide_page_content(g, root="../"),
            footer=render_footer("../"),
        )
        (GUIDES_OUT / f"{g['slug']}.html").write_text(page, encoding="utf-8")
        print(f"wrote {(GUIDES_OUT / (g['slug'] + '.html')).relative_to(ROOT)}")

    featured = next((g for g in guides if g["featured"]), None)
    grid = [g for g in guides if not g["featured"]]
    index_page = PAGE.format(
        page_title="Free Guides | Parenthood.ai",
        page_description="Free, practical guides and prompt packs that turn AI into real help for your family. No jargon, no fluff.",
        og_type="website",
        og_url="https://theparenthoodai.com/guides/",
        root="../",
        nav=render_nav("../", active="guides"),
        content=guides_index_content(featured, grid),
        footer=render_footer("../"),
    )
    (GUIDES_OUT / "index.html").write_text(index_page, encoding="utf-8")
    print(f"wrote {(GUIDES_OUT / 'index.html').relative_to(ROOT)}")


def main():
    build_blog()
    build_guides()


if __name__ == "__main__":
    main()
