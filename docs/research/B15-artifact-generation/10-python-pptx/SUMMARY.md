# SUMMARY — python-pptx (programmatic PowerPoint generation)

## Full citation
- **Title:** *python-pptx — Python library for creating and updating PowerPoint (.pptx) files*
- **Author/Org:** Steve Canny (maintainer) and contributors (OSS, MIT).
- **Year:** v1.0.0 line, actively maintained as of 2026.
- **Venue:** Official documentation (primary source for capability).
- **URL/DOI:** https://python-pptx.readthedocs.io/

## Questions informed
- **L1.B15.2** (the programmatic-generation half of deck craft).

## GRADE tier
**Moderate–High** (official docs = primary for capability facts; corroborated by independent how-to sources). Directly verifiable against the library.

## Key claims (faithful)
1. Creates/reads/updates **.pptx** (OOXML PresentationML, Office 2007+) **without PowerPoint installed** — suited to automation/report generation.
2. **Placeholders:** pictures, tables, and charts can be inserted into a slide-layout placeholder, taking its position/size and some formatting. The reliable way to address a placeholder is by its **idx** (stable integer key inherited from the layout).
3. **Charts:** supports common 2D chart types (column, bar, line, pie, and others); **3D types are not supported**. Default series colours are the **theme Accent 1–6**, in order; specific colours can be assigned to points/series for some chart types.
4. **Content:** insert text boxes, images, shapes, tables, charts programmatically; load a template and replace placeholder text / named shapes while injecting dynamic charts/images (template + data-merge pattern).
5. **Limitations:** native HTML support is limited; advanced formatting python-pptx does not expose directly can be reached by **manipulating the underlying Open XML** (the OOXML escape hatch — source 12).

## Reproducibility note
Placeholder-by-idx, supported chart types (no 3D), theme Accent 1–6 defaults, and the raw-XML escape hatch are stated in the official docs and corroborated by independent tutorials (GeeksforGeeks, SoftKraft, fileformat.com). Cross-checked 2026-06-15.
