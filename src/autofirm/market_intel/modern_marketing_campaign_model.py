"""A focused, typed model of modern / social marketing campaigns and channels.

What this does
--------------
Defines the deterministic data model for the modern-marketing engine:

* :class:`ChannelKind` — the Paid / Owned / Earned (POE) taxonomy, the canonical
  channel framing from the B7 marketing research (Forrester 2009; adopted in
  ``docs/research/B7-marketing-foundations``), specialised to modern social
  surfaces (paid social, organic social, influencer/earned, owned email/site).
* :class:`Channel` — one campaign channel: its kind and a sanitized creative
  message. The message is UNTRUSTED (it may originate from a feed/LLM draft) and is
  sanitized at construction so an injection payload can never ride into a campaign.
* :class:`MarketingCampaign` — a named campaign over one or more channels, with a
  derived :meth:`channel_mix` (the POE split) so brand/activation balance is
  inspectable.

Why it exists / where it sits
-----------------------------
This is the "act" surface of the market-intel loop: once the green-light gate says
GO, a campaign is the modern/social marketing expression of that decision. It is
deliberately FOCUSED — typed model + POE mix only, not a full marketing-automation
stack — per the brief "do not overbuild".

Security / compliance invariants upheld
---------------------------------------
* **Untrusted creative (§5.6):** every channel message passes
  ``sanitize_untrusted_signal`` at construction; an injection/oversized payload is
  refused fail-closed, never embedded in a live campaign.
* **Determinism (§3.11):** the POE channel mix is a pure function of the channels.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from autofirm.market_intel.untrusted_signal_sanitizer import sanitize_untrusted_signal

__all__ = ["Channel", "ChannelKind", "MarketingCampaign"]


class ChannelKind(StrEnum):
    """The modern-social specialisation of the Paid / Owned / Earned taxonomy.

    POE is the canonical channel framing from the B7 research (Forrester 2009).
    Each modern channel maps to exactly one POE class via :meth:`poe_class`, so the
    campaign's paid/owned/earned mix is unambiguous.
    """

    PAID_SOCIAL = "paid_social"  # paid placements on social platforms
    ORGANIC_SOCIAL = "organic_social"  # owned organic posting on social
    INFLUENCER = "influencer"  # earned/influencer advocacy
    OWNED_EMAIL = "owned_email"  # owned email/CRM
    OWNED_SITE = "owned_site"  # owned site/blog/landing

    def poe_class(self) -> str:
        """Return the Paid / Owned / Earned class this channel belongs to."""
        # A total mapping: every member resolves to exactly one POE class, so the
        # campaign mix below is exhaustive and deterministic.
        return {
            ChannelKind.PAID_SOCIAL: "paid",
            ChannelKind.ORGANIC_SOCIAL: "owned",
            ChannelKind.INFLUENCER: "earned",
            ChannelKind.OWNED_EMAIL: "owned",
            ChannelKind.OWNED_SITE: "owned",
        }[self]


class Channel(BaseModel):
    """One campaign channel: a POE-classified kind and a sanitized message.

    ``message`` is UNTRUSTED creative copy (it may be a feed-derived or LLM-drafted
    draft). It is sanitized at construction, so a constructed :class:`Channel`
    always carries clean, bounded, single-line copy — never a raw injection vector.
    """

    model_config = ConfigDict(frozen=True)

    kind: ChannelKind
    message: str  # sanitized at construction (see validator) — trusted thereafter

    @field_validator("message")
    @classmethod
    def _sanitize_message(cls, value: str) -> str:
        # fail-closed (§5.6): treat campaign creative as untrusted input. Reuse the
        # one boundary sanitizer so oversized/injection-laden copy is REFUSED here
        # (it raises SignalRejectedError) rather than published into a campaign.
        return sanitize_untrusted_signal(value)


class MarketingCampaign(BaseModel):
    """A named modern-marketing campaign over one or more POE-classified channels.

    The derived :meth:`channel_mix` exposes the paid/owned/earned split so the
    brand-vs-activation balance (B7 research) is inspectable without re-deriving it.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    channels: tuple[Channel, ...]

    @field_validator("name")
    @classmethod
    def _name_non_empty(cls, value: str) -> str:
        # fail-closed: an unnamed campaign cannot be referenced or audited.
        if not value.strip():
            raise ValueError("campaign name must be non-empty")
        return value

    @model_validator(mode="after")
    def _at_least_one_channel(self) -> MarketingCampaign:
        # fail-closed: a campaign with no channel can reach no audience — refuse it
        # rather than silently shipping a no-op campaign.
        if not self.channels:
            raise ValueError("campaign must have at least one channel")
        return self

    def channel_mix(self) -> dict[str, int]:
        """Return the count of channels per POE class (paid / owned / earned).

        A pure, deterministic reduction over :attr:`channels`; every POE class is
        present in the result (zero when unused) so callers need not special-case
        a missing key.
        """
        mix = {"paid": 0, "owned": 0, "earned": 0}
        for channel in self.channels:
            mix[channel.kind.poe_class()] += 1
        return mix
