"""Synthetic builders + strategies for the substrate test suites (no real process).

Everything here is deterministic and process-free: a fixed clock, secret-free
credential-reference builders, a real :class:`ScopedCredential` carrying a
high-entropy SENTINEL secret (so secret-leak scans cannot collide with English
words in the audit vocabulary), a leak-scanning fake launcher, and Hypothesis
strategies for spawn/handoff/resume sequences. NO network, NO real ``claude``
process, NO real secrets — exactly the substrate's testability contract.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from hypothesis import strategies as st

from autofirm.access.credential_scope_contract import (
    CredentialScope,
    Operation,
    RedactedSecret,
    ScopedCredential,
)
from autofirm.org.org_identifiers import RoleId, SequentialIdGenerator
from autofirm.substrate.context_budget_state import ContextBudgetState
from autofirm.substrate.regrounded_saga_state import RegroundedSagaState
from autofirm.substrate.scoped_credential_reference import ScopedCredentialReference
from autofirm.substrate.session_launcher_protocol import (
    FakeSessionLauncher,
    LaunchResult,
    LaunchSpec,
)
from autofirm.substrate.session_lifecycle_engine import SessionLifecycleEngine

# A fixed UTC instant; credential references built below expire well after it so a
# spawn at this clock is never refused for the wrong reason in happy-path tests.
FIXED_NOW = datetime(2026, 6, 16, 12, 0, 0, tzinfo=UTC)

# High-entropy sentinel prefix for any secret we plant: it cannot occur in the
# substrate's fixed vocabulary (flag names, JSON keys, ISO timestamps), so a
# substring hit on a session/handoff/repr blob can ONLY mean the secret leaked.
SECRET_SENTINEL = "ZZSUBSECRETZZ-"


class FrozenNow:
    """A deterministic clock returning ``start``, optionally advancing per call."""

    def __init__(self, start: datetime = FIXED_NOW, step: timedelta = timedelta(0)) -> None:
        """Seed at ``start``, advancing ``step`` on each ``now()``."""
        self._current = start
        self._step = step

    def now(self) -> datetime:
        value = self._current
        self._current = self._current + self._step
        return value


def make_credential_reference(
    *,
    component: str = "agent",
    resource: str = "pg:db",
    operations: tuple[str, ...] = ("READ",),
    tenant_id: str = "tenant-1",
    expires_at: datetime = FIXED_NOW + timedelta(minutes=30),
) -> ScopedCredentialReference:
    """Build a valid, secret-free credential reference (defaults are non-expired)."""
    return ScopedCredentialReference(
        component=component,
        resource=resource,
        operations=operations,
        tenant_id=tenant_id,
        expires_at=expires_at,
    )


def make_scoped_credential_with_sentinel(
    secret_tail: str = "abc123",
    *,
    expires_at: datetime = FIXED_NOW + timedelta(minutes=30),
) -> ScopedCredential:
    """Build a REAL credential whose secret is a unique sentinel value.

    Used by the secrets-never-logged suite: the returned credential's secret is
    ``SECRET_SENTINEL + secret_tail``, reachable only via ``reveal()``. Building a
    reference from it (``from_scoped_credential``) must never carry the secret.
    """
    return ScopedCredential(
        component="agent",
        scope=CredentialScope(
            resource="pg:db", operations=frozenset({Operation.READ}), tenant_id="tenant-1"
        ),
        secret=RedactedSecret(secret_value=SECRET_SENTINEL + secret_tail),
        issued_at=FIXED_NOW,
        expires_at=expires_at,
    )


def make_budget(
    *, limit: int = 1000, consumed: int = 0, threshold: float = 0.8
) -> ContextBudgetState:
    """Build a context budget (defaults: 1000-token window, 80% handoff threshold)."""
    return ContextBudgetState(
        limit_tokens=limit, consumed_tokens=consumed, handoff_threshold=threshold
    )


def make_saga_state(
    *, work_complete: bool = False, goal: str = "build the thing"
) -> RegroundedSagaState:
    """Build a re-grounded saga state (defaults: incomplete work, a real goal)."""
    return RegroundedSagaState(
        goal_verbatim=goal,
        application_state="git@abc123",
        operation_state="step 3 of 5",
        dependency_state="awaiting nothing",
        work_complete=work_complete,
    )


def make_engine(
    *, clock: FrozenNow | None = None
) -> tuple[SessionLifecycleEngine, FakeSessionLauncher]:
    """Wire an engine to a deterministic fake launcher + clock; return both.

    The fake launcher is returned so tests can assert which specs it was asked to
    launch (and that no secret was ever passed to it).
    """
    launcher = FakeSessionLauncher(SequentialIdGenerator())
    engine = SessionLifecycleEngine(
        launcher=launcher,
        clock=clock or FrozenNow(),
        id_generator=SequentialIdGenerator(),
    )
    return engine, launcher


class LeakScanningLauncher:
    """A fake launcher that records every spec AND scans it for a planted secret.

    Wraps the deterministic id allocation of :class:`FakeSessionLauncher` but, on
    each launch, asserts the planted ``forbidden_secret`` appears nowhere in the
    spec's serialized form — proving the secret never reaches the spawn boundary.
    """

    def __init__(self, forbidden_secret: str) -> None:
        """Refuse to ever see ``forbidden_secret`` in any launched spec."""
        self._inner = FakeSessionLauncher(SequentialIdGenerator())
        self._forbidden = forbidden_secret

    def launch(self, spec: LaunchSpec) -> LaunchResult:
        # secrets-never-logged: a spec is structurally secret-free; assert it over
        # every projection a log/audit could plausibly capture (repr + model_dump).
        blob = f"{spec!r} {spec.model_dump()} {spec.model_dump_json()}"
        assert self._forbidden not in blob, "secret leaked into a launch spec"
        return self._inner.launch(spec)

    def launched_specs(self) -> tuple[LaunchSpec, ...]:
        """Return every spec launched (delegates to the inner fake)."""
        return self._inner.launched_specs()


# --- Hypothesis strategies (synthetic, bounded) ------------------------------

role_id_strategy = st.builds(
    RoleId,
    st.text(
        alphabet=st.characters(min_codepoint=33, max_codepoint=126),
        min_size=1,
        max_size=16,
    ),
)

# A small pool of distinct working dirs so the single-writer property is exercised
# (collisions are intentional — they force the engine's refusal path).
working_dir_strategy = st.sampled_from(["/wt/a", "/wt/b", "/wt/c"])

token_strategy = st.integers(min_value=0, max_value=5000)
