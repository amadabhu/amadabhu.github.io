## Contact
- [first].[last]@[gmail,protonmail].com


# my super dope website 

Source for [achyuthmadabhushi.com](https://achyuthmadabhushi.com). Jekyll‑flavored templates rendered by GitHub Pages on push, plus a small Python preview pipeline for local iteration without installing Ruby.

## Layout

```
.
├── _config.yml             # Jekyll site config
├── Gemfile                 # for the Ruby/Jekyll path (deploy)
├── _layouts/               # default page shell
├── _includes/              # header, footer, project list, timeline, guides, substack feed
├── content/                # ALL writable text — see below
├── assets/                 # css, js, images, resumes, school logos
│   └── logos/              # flat-named logos for timeline cards
├── scripts/                # python preview pipeline
└── .github/workflows/      # Substack feed refresher
```

## `content/` — single source of truth for writable text

```
content/
├── index.md                # /            — home page
├── musings.md              # /musings/    — long-form bio with sticky TOC
├── projects.md             # /projects/   — wraps the projects collection
├── timeline.md             # /timeline/   — wraps the timeline collection
├── guides.md               # /guides/     — wraps the PDF guides collection
├── projects/               # COLLECTION — one .md per project
│   ├── enterprise-rag.md
│   ├── wifx.md
│   ├── notebook2ppt.md
│   ├── toolbox.md
│   └── data-structures-algorithms.md
├── timeline/               # COLLECTION — one .md per career / education entry
│   ├── udel.md
│   ├── nasa.md
│   ├── ...
│   └── steampunk.md
└── quick-reference-guides/ # BINARY COLLECTION — PDFs, auto-rendered as cards
    ├── Python_CheatSheet_*.pdf
    ├── ML_cheat_sheet.pdf
    └── ...
```

**Pages**: top‑level `.md` files in `content/` are pages. Each declares its own `permalink:` in frontmatter; the URL is independent of the file path.

**Collections**: subdirectories are auto‑discovered as collections. Every `.md` file inside becomes one item in `site.<dirname>` (with hyphens converted to underscores so dotted access works in Liquid). Frontmatter holds metadata (slug, status, dates, stack, links, logo, …); the markdown body becomes the long‑form description.

**Binary collections**: non‑markdown files inside a content subdirectory (currently just PDFs in `content/quick-reference-guides/`) get exposed as `site.<dirname>_files`, with auto‑humanized display names, file size, and URL. The `/guides/` page renders these as cards with iframe previews + download buttons.

## Local development

GitHub Pages does the canonical Jekyll build on push. For local preview without Ruby, the repo ships a Python pipeline:

```bash
python3 -m venv .venv
.venv/bin/pip install python-liquid markdown pyyaml

.venv/bin/python scripts/serve.py
# → http://localhost:8000
```

`scripts/serve.py` is the only command you need day‑to‑day:

- runs `scripts/build_site.py` at startup,
- watches `content/`, `_data/`, `_layouts/`, `_includes/`, `_config.yml`, and `scripts/build_site.py` itself,
- rebuilds automatically on the next request whenever a watched file changes,
- hot‑reloads the build script's own module if you edit it (no server restart needed),
- serves rendered HTML from `_site/` and overlays `/assets/*` and `/<binary-collection>/*.pdf` straight from their source directories — no copy or symlink under `_site/`.

If you'd rather use real Jekyll: install Ruby ≥ 3.1 (`rbenv install 3.3` or similar), then `bundle install && bundle exec jekyll serve`.

### Build pipeline at a glance

```
content/*.md, _data/, _layouts/, _includes/   ─►  scripts/build_site.py  ─►  _site/*.html
                                                                            (gitignored)
content/<collection>/*.md   ─►   site.<collection>      (frontmatter + rendered HTML body)
content/<collection>/*.pdf  ─►   site.<collection>_files (filename, name, url, size_label)
```

Inside `build_site.py`:

- A `JekyllizingLoader` (subclass of python-liquid's FileSystemLoader) preprocesses include files at load time — rewriting Jekyll-specific `{% include foo.html bar=baz %}` and `{{ include.x }}` syntax into the standard-Liquid forms python-liquid expects.
- `feed_meta` and `seo` Jekyll-plugin tags get stripped.
- Filters: `relative_url`, `absolute_url`, `markdownify`, `where`, `date`.

## Refreshing the Substack feed

Automatic every 6 hours via [.github/workflows/refresh-substack.yml](.github/workflows/refresh-substack.yml). To run on demand: **Actions → Refresh Substack feed → Run workflow**. To run locally: `python3 scripts/build_substack_feed.py` — uses stdlib only, regenerates `_includes/substack-feed.html`.

## Editing flow

| Want to | Edit |
|---|---|
| Change page prose | the matching top-level `content/*.md` |
| Add or edit a project | a file in `content/projects/<slug>.md` |
| Add or edit a career/education entry | a file in `content/timeline/<year>-<org>.md` |
| Add a downloadable PDF guide | drop the file in `content/quick-reference-guides/`; it appears on `/guides/` automatically |
| Change site-wide nav | `_includes/header.html` |
| Change the visual theme | `assets/css/site.css` (search section headers like `===== Timeline =====`) |
| Add a new top-level page | new `content/<name>.md` with `permalink: /<name>/` and a nav entry in `_includes/header.html` |
| Add a new collection | create `content/<name>/` with `.md` files inside; reference as `site.<name>` in templates |

## Deployment

GitHub Pages builds and serves from the `main` branch root. Ensure repo Settings → Pages source is set to `main` / `/ (root)` — the legacy `/docs` source has been retired.

