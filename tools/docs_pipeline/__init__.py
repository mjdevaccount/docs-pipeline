"""
docs_pipeline
=============

Lightweight orchestration layer for:

- Generating architecture views from Structurizr DSL (via structurizr_tools)
- Rendering Markdown documents to PDF/HTML/DOCX (via pdf tools)

The initial implementation is intentionally minimal: it shells out to the
existing `cli/main.py` CLI for rendering while using the new SOLID-style
`structurizr_tools` API for diagram export. This keeps the pipeline simple
today while leaving room for a richer internal API or HTTP service tomorrow.
"""


