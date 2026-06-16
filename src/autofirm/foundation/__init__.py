"""Foundation layer — primitive, dependency-free building blocks.

Houses the exact-arithmetic and other low-level primitives that every higher
pipeline stage relies on. Determinism and exactness-to-the-unit are mandatory
here (CLAUDE.md §3.11): a single numerical error on these paths is a defect.
"""
