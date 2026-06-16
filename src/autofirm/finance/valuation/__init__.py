"""Valuation engine — DCF, terminal value, NPV and IRR.

Intrinsic valuation by discounting projected free cash flows at a discount rate
(WACC), with a Gordon-growth terminal value, plus investment-appraisal metrics
(NPV, IRR). All arithmetic is exact :class:`~decimal.Decimal` at a wide fixed
precision and deterministic; every formula cites Damodaran (research source 01).
Malformed inputs are refused fail-closed (CLAUDE.md §3.11 / §5.6).
"""
