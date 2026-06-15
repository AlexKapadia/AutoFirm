# BEST-PARTS — OOXML Standard

## ADOPT
- **OOXML/OPC is the universal substrate** for all three artifact types — one mental model (ZIP of XML parts) governs Excel/PowerPoint/Word generation. All three builders emit OPC packages.
- **Escape hatch:** when a Python lib cannot express a needed feature, **edit the underlying Open XML part directly** (standards-backed). Keeps "institution-grade, not templated" achievable without being capped by library defaults.
- **Standards-conformance as a validation axis:** generated files must be valid OPC/OOXML (open without repair in Excel/PowerPoint/Word). A `file_opens_clean` smoke test per artifact (open via LibreOffice headless; assert valid package, no repair prompt).

## REJECT
- **Legacy binary formats** (.xls/.ppt/.doc) — superseded; generate only OOXML (.xlsx/.pptx/.docx) for forward-compatibility and standard conformance.

## BUILD IMPLICATION
Cross-cutting contract: every builder outputs **valid OPC/OOXML**, verified by a headless open-without-repair test. The raw-XML escape hatch is the sanctioned mechanism for premium, non-templated formatting beyond library defaults — directly serving the anti-AI-slop bar.
