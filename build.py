#!/usr/bin/env python3
"""Regenerates blog/index.html and blog/<slug>.html from content/blog/*.md.

Run this after adding or editing a post in content/blog/, then commit the
regenerated HTML. Netlify serves plain static files, no build step there.
"""
import re
from pathlib import Path
from html import escape

ROOT = Path(__file__).parent
CONTENT_DIR = ROOT / "content" / "blog"
OUTPUT_DIR = ROOT / "blog"

NAV = """  <div class="site-nav">
    <a href="{root}index.html" style="display:flex;align-items:center;gap:10px">
      <img class="nav-logo" src="{root}assets/img/logo-mark.png" alt="Parenthood.ai" style="height:40px;width:auto">
      <span class="serif brand-word" style="font-size:22px;font-weight:600;color:var(--charcoal-900);letter-spacing:.01em">parenthood<span style="color:var(--terracotta-500)">.ai</span></span>
    </a>
    <div class="nav-links" style="display:flex;align-items:center;gap:30px">
      <a class="navlink" href="{root}index.html#guides-section">Free guides</a>
      <a class="navlink" href="{root_or_dot}" style="color:var(--terracotta-500)">Blog</a>
      <a class="navlink" href="{root}index.html#about">About</a>
    </div>
  </div>"""

FOOTER = """  <div class="site-footer">
    <div class="footer-inner">
      <div class="footer-cols">
        <div>
          <span class="serif" style="font-size:24px;font-weight:600;color:var(--cream-100)">parenthood<span style="color:var(--terracotta-400)">.ai</span></span>
          <p style="margin:12px 0 0;font-size:13px;line-height:1.6;color:rgba(241,236,233,.6);max-width:260px">Simplifying life with help from AI. One simple win at a time.</p>
        </div>
        <div class="footer-col"><span class="wm" style="color:var(--sand-400);margin-bottom:4px">EXPLORE</span><a href="{root}index.html#guides-section" style="color:inherit">Free guides</a><span>The shop</span><a href="{root_or_dot}" style="color:inherit">Blog</a><a href="{root}index.html#about" style="color:inherit">About</a></div>
        <div class="footer-col"><span class="wm" style="color:var(--sand-400);margin-bottom:4px">SUPPORT</span><span>Contact</span><span>FAQ</span><span>License</span></div>
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
      <div style="border:1px dashed var(--border-default);border-radius:16px;padding:32px 34px;opacity:.6;text-align:center">
        <span class="mono" style="font-size:11px;letter-spacing:.14em;color:var(--sand-400)">MORE POSTS COMING SOON</span>
      </div>
    </div>
  </div>"""

CARD = """      <a href="{slug}.html" class="lift" style="display:block;background:var(--surface-card);border:1px solid var(--border-subtle);border-radius:16px;padding:32px 34px;color:inherit">
        <div class="mono" style="font-size:11px;letter-spacing:.1em;color:var(--sand-400);margin-bottom:10px">{date_upper}</div>
        <h2 class="serif" style="margin:0 0 10px;font-weight:600;font-size:28px;line-height:1.15;color:var(--charcoal-900)">{title}</h2>
        <p style="margin:0 0 16px;font-size:14.5px;line-height:1.6;color:var(--charcoal-500)">{excerpt}</p>
        <span style="font-size:13px;font-weight:600;color:var(--terracotta-500)">Read →</span>
      </a>"""


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug


def parse_post(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not match:
        raise ValueError(f"{path} is missing frontmatter")
    frontmatter, body = match.groups()
    meta = {}
    for line in frontmatter.splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip().strip('"')

    paragraphs = [p.strip() for p in body.strip().split("\n\n") if p.strip()]
    body_html = "\n".join(f"        <p>{escape(p)}</p>" for p in paragraphs)
    excerpt_source = paragraphs[0] if paragraphs else ""
    excerpt = excerpt_source if len(excerpt_source) <= 160 else excerpt_source[:157].rsplit(" ", 1)[0] + "..."

    return {
        "title": meta["title"],
        "date": meta["date"],
        "slug": slugify(meta["title"]),
        "body_html": body_html,
        "excerpt": excerpt,
    }


def main():
    posts = [parse_post(p) for p in sorted(CONTENT_DIR.glob("*.md"))]
    OUTPUT_DIR.mkdir(exist_ok=True)

    for post in posts:
        content = ARTICLE_CONTENT.format(
            title=escape(post["title"]),
            date=escape(post["date"]).upper(),
            body_html=post["body_html"],
        )
        page = PAGE.format(
            page_title=f"{post['title']} | Parenthood.ai",
            page_description=escape(post["excerpt"]),
            root="../",
            nav=NAV.format(root="../", root_or_dot="./index.html"),
            content=content,
            footer=FOOTER.format(root="../", root_or_dot="./index.html"),
        )
        out_path = OUTPUT_DIR / f"{post['slug']}.html"
        out_path.write_text(page, encoding="utf-8")
        print(f"wrote {out_path.relative_to(ROOT)}")

    cards = "\n".join(
        CARD.format(
            slug=post["slug"],
            date_upper=escape(post["date"]).upper(),
            title=escape(post["title"]),
            excerpt=escape(post["excerpt"]),
        )
        for post in posts
    )
    index_page = PAGE.format(
        page_title="The Blog | Parenthood.ai",
        page_description="Honest writing about learning AI as a parent, one step at a time.",
        root="../",
        nav=NAV.format(root="../", root_or_dot="./index.html"),
        content=INDEX_CONTENT.format(cards=cards),
        footer=FOOTER.format(root="../", root_or_dot="./index.html"),
    )
    index_path = OUTPUT_DIR / "index.html"
    index_path.write_text(index_page, encoding="utf-8")
    print(f"wrote {index_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
