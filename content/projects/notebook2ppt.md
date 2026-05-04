---
order: 3
slug: notebook2ppt
name: notebook2ppt
status: public
highlight: true
one_liner: Convert a Jupyter notebook into a PowerPoint deck — headings become slides, figures and tables flow into the layout.
stack:
  - Python
  - nbformat
  - python-pptx
  - Pillow
  - pytest
links:
  - { label: "GitHub", url: "https://github.com/amadabhu/Notebook2ppt" }
---

`nbconvert --to slides` produces reveal.js HTML, which is great in the browser
and useless when somebody on the other side of the org wants a `.pptx` they
can edit. **notebook2ppt** fills the gap: read the notebook you already wrote,
write a real PowerPoint file.

The mapping is **heading-driven** — `#` and `##` markdown headings open
slides; markdown bodies, matplotlib PNGs, pandas HTML tables, and stream
outputs become typed `Block`s placed by a python-pptx renderer. A two-stage
pipeline (notebook → IR → .pptx) keeps extraction independent of layout, so
swapping in a different render target later (Google Slides, reveal.js, plain
HTML) doesn't require redoing the parsing work.

Ships with a CLI (`notebook2ppt analysis.ipynb -o deck.pptx`), a Python
library, three example notebooks with real baked-in outputs, and a small
pytest suite.
