---
order: 1
slug: personal-site
name: amadabhu.github.io
status: shipped
highlight: true
one_liner: This site, a Jekyll-flavored personal site with a small Python build pipeline so it renders without Ruby.
stack:
  - Jekyll
  - Liquid
  - Python
  - Markdown
  - GitHub Pages
links:
  - { label: "GitHub", url: "https://github.com/amadabhu/amadabhu.github.io" }
  - { label: "Live", url: "https://achyuthmadabhushi.com" }
---

The site you're reading. Templates are Jekyll-flavored Liquid + Markdown, but the build runs through a small Python pipeline (`scripts/build_site.py`) so I can iterate locally without installing Ruby. GitHub Actions runs the same Python build on push and deploys the artifact to Pages.
