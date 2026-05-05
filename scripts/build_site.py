#!/usr/bin/env python3
"""Render the Jekyll-flavored site into _site/ for local preview.

This is a *preview* renderer. GitHub Pages itself runs the canonical Jekyll
build on push. The point of this script is to let you eyeball changes locally
without installing Ruby — it implements just enough of Jekyll's Liquid +
Markdown pipeline to render this specific site.

Usage:
    python3 scripts/build_site.py
    python3 scripts/serve.py
"""

from __future__ import annotations

import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import markdown as md_lib
import yaml
from liquid import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
OUT = ROOT / "_site"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


def load_config() -> dict:
    return yaml.safe_load((ROOT / "_config.yml").read_text())


def load_data() -> dict:
    data = {}
    data_dir = ROOT / "_data"
    if not data_dir.exists():
        return data
    for f in data_dir.glob("*.yml"):
        data[f.stem] = yaml.safe_load(f.read_text())
    return data


_TRAILING_DIGITS_RE = re.compile(r"[_\-\s]\d{6,}$")
_CAMEL_RE = re.compile(r"(?<=[a-z])(?=[A-Z])")
_ACRONYMS = {"Sql", "Ml", "Ai", "Ipv6", "Tcpip", "Aws"}
_ACRONYM_FIX = {"Sql": "SQL", "Ml": "ML", "Ai": "AI", "Ipv6": "IPv6", "Tcpip": "TCP/IP", "Aws": "AWS"}


def humanize_filename(stem: str) -> str:
    """Best-effort prettifier for PDF basenames.

    `Data_Science_Cheat_Sheet_1628197365` -> `Data Science Cheat Sheet`
    `MachineLearningCheatsheet`           -> `Machine Learning Cheatsheet`
    `ipv6_tcpip_pocketguide`              -> `IPv6 TCP/IP Pocketguide`
    """
    name = _TRAILING_DIGITS_RE.sub("", stem)
    name = _CAMEL_RE.sub(" ", name)
    name = name.replace("_", " ").replace("-", " ").strip()
    parts = [p for p in name.split() if p]
    parts = [p[0].upper() + p[1:].lower() for p in parts]
    parts = [_ACRONYM_FIX.get(p, p) for p in parts]
    return " ".join(parts)


def load_collections() -> dict:
    """Load each subdirectory of content/ as a collection.

    Every .md file in `content/<name>/` is parsed into a dict that merges its
    frontmatter with a `body` field holding the rendered-HTML body. Items are
    sorted by frontmatter `order` if present, otherwise by filename. The result
    is exposed in templates as `site.<name>` (e.g. `site.projects`).

    Non-markdown files in those directories (e.g. PDFs) are exposed as a
    parallel list at `site.<name>_files`, so a template can render previews
    or download cards for them.
    """
    collections = {}
    files_index = {}
    if not CONTENT.exists():
        return collections
    for sub in sorted(CONTENT.iterdir()):
        if not sub.is_dir():
            continue
        items = []
        for md_path in sorted(sub.glob("*.md")):
            text = md_path.read_text()
            meta, body = parse_frontmatter(text)
            item = dict(meta)
            item["body"] = render_markdown(body.strip())
            item["_filename"] = md_path.stem
            items.append(item)
        if any("order" in it for it in items):
            items.sort(key=lambda it: it.get("order", 10**9))
        # Normalize directory name into a Liquid-safe identifier (hyphens
        # break dotted access in templates) — `quick-reference-guides`
        # becomes `quick_reference_guides`.
        key = sub.name.replace("-", "_")
        collections[key] = items

        files = []
        for f in sorted(sub.iterdir()):
            if not f.is_file() or f.suffix.lower() == ".md" or f.name.startswith("."):
                continue
            size = f.stat().st_size
            # URL-encode the path components so spaces, '+', and other URL-
            # significant chars in user-supplied filenames don't break links.
            from urllib.parse import quote
            url = f"/{quote(sub.name)}/{quote(f.name)}"
            files.append({
                "filename": f.name,
                "name": humanize_filename(f.stem),
                "url": url,
                "ext": f.suffix.lstrip(".").lower(),
                "size_bytes": size,
                "size_label": f"{size / 1024 / 1024:.1f} MB" if size >= 1024 * 1024 else f"{size // 1024} KB",
            })
        if files:
            files_index[key + "_files"] = files

    collections.update(files_index)
    return collections


def parse_frontmatter(text: str) -> tuple[dict, str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    return yaml.safe_load(m.group(1)) or {}, m.group(2)


_HIDDEN_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+hidden[ \t]*$", re.IGNORECASE)
_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+\S")


def strip_hidden_sections(text: str) -> str:
    """Drop any markdown section whose heading text is exactly "hidden".

    A section runs from a `# hidden` (any level) heading until the next
    heading of equal-or-higher level, or end of document. Useful for keeping
    private notes alongside published content in the same source file.
    """
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        m = _HIDDEN_HEADING_RE.match(lines[i].rstrip("\n"))
        if not m:
            out.append(lines[i])
            i += 1
            continue
        level = len(m.group(1))
        i += 1
        while i < n:
            m2 = _HEADING_RE.match(lines[i])
            if m2 and len(m2.group(1)) <= level:
                break
            i += 1
    return "".join(out)


def render_markdown(text: str) -> str:
    return md_lib.markdown(
        strip_hidden_sections(text),
        extensions=["extra", "fenced_code", "tables", "sane_lists", "toc"],
        output_format="html5",
    )


class JekyllizingLoader(FileSystemLoader):
    """FileSystemLoader that runs `jekyllize` on every template it loads.

    Without this, Jekyll-syntax includes (`{% include foo.html bar=baz %}` and
    `{{ include.x }}` lookups inside foo.html) work in the calling template
    but not when foo.html is itself loaded — the loader returns raw bytes
    that python-liquid then parses with its stricter rules.
    """

    def get_source(self, env, name, **kwargs):
        source, *rest = super().get_source(env, name, **kwargs)
        return (jekyllize(source), *rest)


def make_env(site: dict) -> Environment:
    env = Environment(loader=JekyllizingLoader(str(ROOT / "_includes")))

    # ---- filters ----
    def relative_url(value):
        baseurl = site.get("baseurl", "") or ""
        if not value:
            return baseurl + "/"
        if value.startswith("/"):
            return baseurl + value
        return baseurl + "/" + value

    def absolute_url(value):
        url = (site.get("url") or "").rstrip("/")
        return url + relative_url(value)

    def markdownify(value):
        return render_markdown(value or "")

    def where(items, key, val):
        if not items:
            return []
        return [i for i in items if i.get(key) == val]

    def date_filter(value, fmt):
        if value == "now" or value is None:
            dt = datetime.now(timezone.utc)
        else:
            dt = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
        # Liquid %-d isn't portable; just sub it out.
        fmt = fmt.replace("%-d", "%d").replace("%-m", "%m")
        return dt.strftime(fmt).lstrip("0") if "%-d" in fmt else dt.strftime(fmt)

    env.add_filter("relative_url", relative_url)
    env.add_filter("absolute_url", absolute_url)
    env.add_filter("markdownify", markdownify)
    env.add_filter("where", where)
    env.add_filter("date", date_filter)

    return env


INCLUDE_TAG_RE = re.compile(
    r"{%-?\s*include\s+(?P<name>[^\s\"'%]+)(?P<rest>[^%]*?)-?%}",
    re.DOTALL,
)
INCLUDE_KW_RE = re.compile(r"(\b[A-Za-z_]\w*)\s*=\s*", re.DOTALL)
INCLUDE_VAR_RE = re.compile(r"\binclude\.([A-Za-z_]\w*)")


PLUGIN_TAG_RE = re.compile(r"{%-?\s*(?:feed_meta|seo)\s*-?%}\s*", re.DOTALL)


def jekyllize(source: str) -> str:
    """Translate Jekyll-flavored Liquid into python-liquid's stricter dialect.

    Jekyll permits two non-standard things inside `{% include ... %}`:
    1. unquoted filenames (`{% include header.html %}`)
    2. `key=value` keyword arguments

    python-liquid wants `{% include "header.html" key: value %}`. This
    function also strips Jekyll-plugin-only tags (`{% feed_meta %}`,
    `{% seo %}`) that have no analog in standard Liquid.
    """

    def _rewrite(match: re.Match) -> str:
        name = match.group("name")
        rest = match.group("rest")
        rest = INCLUDE_KW_RE.sub(r"\1: ", rest)
        return '{% include "' + name + '" ' + rest.strip() + " %}"

    source = PLUGIN_TAG_RE.sub("", source)
    source = INCLUDE_TAG_RE.sub(_rewrite, source)
    # Jekyll exposes include params as `include.x`; python-liquid scopes them
    # as bare locals. Rewrite so the Jekyll syntax resolves correctly.
    source = INCLUDE_VAR_RE.sub(r"\1", source)
    return source


def render_page(env: Environment, site: dict, src: Path, body: str, page_meta: dict) -> str:
    page_meta = dict(page_meta)
    permalink = page_meta.get("permalink", "/" + src.stem + "/")
    page_meta.setdefault("url", permalink)

    body_template = env.from_string(jekyllize(body))
    rendered_body = body_template.render(site=site, page=page_meta, content="")

    if src.suffix == ".md":
        rendered_body = render_markdown(rendered_body)

    layout_name = page_meta.get("layout", "default")
    layout_path = ROOT / "_layouts" / f"{layout_name}.html"
    layout_template = env.from_string(jekyllize(layout_path.read_text()))
    return layout_template.render(site=site, page=page_meta, content=rendered_body)


def write_page(html: str, permalink: str) -> None:
    target_dir = OUT / permalink.strip("/")
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "index.html").write_text(html, encoding="utf-8")


# For local preview, scripts/serve.py overlays /assets/* and /<dir>/* directly
# from the source directories (no copies in _site/). For production deploy via
# GitHub Actions, _site/ needs to be self-contained, so the build step below
# copies assets, binary-collection files, CNAME, and a .nojekyll marker into it.


def copy_static_outputs() -> None:
    # assets/
    src_assets = ROOT / "assets"
    if src_assets.exists():
        dst_assets = OUT / "assets"
        if dst_assets.exists():
            shutil.rmtree(dst_assets)
        shutil.copytree(
            src_assets,
            dst_assets,
            ignore=shutil.ignore_patterns("*.zip", ".DS_Store", ".git*"),
        )

    # Binary files inside content/<collection>/ (recursively) →
    # /<collection>/<...relative path...>/<file>. Recursion lets a collection
    # group binaries into subfolders (e.g. `content/timeline/Resume/x.pdf`
    # served at `/timeline/Resume/x.pdf`).
    if CONTENT.exists():
        for sub in sorted(CONTENT.iterdir()):
            if not sub.is_dir():
                continue
            for f in sub.rglob("*"):
                if not f.is_file():
                    continue
                if f.suffix.lower() == ".md" or f.name.startswith("."):
                    continue
                rel = f.relative_to(sub)
                dst = OUT / sub.name / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dst)

    # CNAME for GH Pages custom domain (if present at repo root)
    cname = ROOT / "CNAME"
    if cname.exists():
        shutil.copy2(cname, OUT / "CNAME")

    # .nojekyll suppresses any GH Pages Jekyll processing of the artifact
    (OUT / ".nojekyll").touch()


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()

    site = load_config()
    site["data"] = load_data()
    site.update(load_collections())
    env = make_env(site)

    pages_built = 0
    if not CONTENT.exists():
        print(f"content/ not found at {CONTENT}", file=sys.stderr)
        return 1
    for md_path in sorted(CONTENT.glob("*.md")):
        text = md_path.read_text()
        meta, body = parse_frontmatter(text)
        permalink = meta.get("permalink") or f"/{md_path.stem}/"
        meta.setdefault("url", permalink)
        html = render_page(env, site, md_path, body, meta)
        write_page(html, permalink)
        pages_built += 1
        print(f"  build  {permalink}  ({md_path.name})")

    copy_static_outputs()

    print(f"\nBuilt {pages_built} pages into {OUT}.")
    print("Serve:  python3 scripts/serve.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
