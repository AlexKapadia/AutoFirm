# Obsidian-Compatible Read-Only View over an Authoritative Graph Store

> Workstream 2 research library — source 6 of 6.
> Method-space cell: **rendering a graph store to a human-navigable backlinked view WITHOUT it being the
> source of truth.**

This is docs/standards-based rather than a single peer-reviewed paper: the Obsidian data model plus the
materialized-view / CQRS read-model pattern.

---

## 1. Full citations

- **Obsidian — Create a vault.** *"A vault is a folder on your local file system where Obsidian stores your
  notes."* <https://obsidian.md/help/Getting+started/Create+a+vault>
- **Obsidian — Internal links.** Wikilink syntax: `[[Three laws of motion]]` or `[[Three laws of motion.md]]`;
  links written by note name/path and resolved by Obsidian. <https://obsidian.md/help/Linking+notes+and+files/Internal+links>
- **Obsidian — Backlinks.** *"A backlink for a note is a link from another note to that note."* The set of
  forward `[[wikilinks]]` across the `.md` files **induces** the bidirectional backlink graph / graph view
  automatically. <https://obsidian.md/help/Plugins/Backlinks>
- **Fowler, M. — CQRS (bliki).** *"you can use a different model to update information than the model you use
  to read information."* The read side is a separate, **derived, rebuildable** representation — not itself
  authoritative; Fowler cautions CQRS "can add significant complexity." <https://martinfowler.com/bliki/CQRS.html>

---

## 2. Faithful structured summary

### Obsidian data model
- **Vault** = a plain **folder of `.md` files** on the local file system.
- **Wikilinks** = `[[Note Name]]` references inside Markdown; resolved by note name/path.
- **Backlink graph** = **derived** from the forward wikilinks — Obsidian computes "which notes link to this
  one" automatically. The graph view is a projection of the link set; it is **not stored separately**.
- Takeaway: an Obsidian-compatible human view is just **Markdown + `[[wikilinks]]` in a folder**, and the
  navigable backlinked graph falls out for free.

### Read-only materialized view / projection (CQRS)
- The **write model** (the authoritative store) and the **read model** (a derived projection optimized for
  reading) are separate. The read model is **rebuildable from the write model** and **never authoritative**.
- *(Flag: Fowler's page does not use the literal term "materialized view"; the materialized-view framing is
  the standard reading of his read-model / ReportingDatabase description, not a verbatim quote.)*

---

## 3. Best parts to take — mapped to the W2 design

| Take this | Into this W2 component |
| --- | --- |
| **Markdown + `[[wikilinks]]` folder = a free, human-navigable, backlinked view.** | The W2 **Obsidian-compatible export VIEW**: emit one `.md` per entity/fact, with `[[wikilinks]]` for every edge. Humans get the backlink graph for free; no graph-DB UI to build. |
| **The backlink graph is DERIVED, never separately authored.** | The export is a pure function of the graph store. Edges → wikilinks; nothing in the vault is hand-edited or fed back. |
| **CQRS: read model is a rebuildable projection, never the source of truth.** | **Hard boundary:** the **graph store is the single source of truth**; the Obsidian vault is a **read-only, fully regenerable projection**. It can be deleted and rebuilt at any time and must **never** be written back into as authority. This directly satisfies the W2 requirement "graph store as source of truth." |
| **CQRS complexity caution.** | Keep the projector dumb and one-directional — a deterministic `store → markdown` renderer with no merge logic. Complexity stays in the store, not the view. |

### RED flags carried forward
- **Bidirectional sync is the trap.** If the vault ever becomes writable-back, you reintroduce the
  "last write wins" clobbering problem (folder 04) and two sources of truth. **Export must be strictly
  read-only and regenerable** — enforce in code (no import path), not by convention.
- Low ops risk overall: a Markdown renderer adds essentially zero standing infrastructure, which is why this
  is the **right** human-facing surface for unattended operation (no DB-backed UI to keep alive).
