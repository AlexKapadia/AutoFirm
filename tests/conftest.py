"""Suite-wide Hypothesis configuration for the AutoFirm test suite.

Why this exists
---------------
The property-based suites (audit Merkle proofs, the inter-agent comms bus, the org
engine) drive many examples over non-trivial hashing/encoding work. Hypothesis's
default 200 ms *per-example wall-clock deadline* is environment-dependent: under
concurrent CI load or several parallel build agents an example can momentarily run
slow and raise ``DeadlineExceeded`` / ``FlakyFailure`` even though the logic is
correct (observed: a Merkle inclusion example took 315 ms once, then 36 ms on the
immediate retry).

Wall-clock timing is **not** a correctness property of this system — determinism is
defined as identical *output* for identical *input*, and that is asserted directly
in the tests. So we disable only the timing deadline suite-wide; we deliberately do
NOT touch ``max_examples`` or any functional/complexity assertion (e.g. the
"proof size is logarithmic" structural check still runs in full). This removes a
flaky, meaningless failure mode without weakening a single correctness check.
"""

from hypothesis import HealthCheck, settings

# Register and load a single project profile. deadline=None drops ONLY the
# environment-dependent wall-clock check; suppressing the too_slow health check
# stops the same timing noise from failing the health-check pass under load.
settings.register_profile(
    "autofirm",
    deadline=None,  # timing is environment-dependent, not a correctness property
    suppress_health_check=[HealthCheck.too_slow],
)
settings.load_profile("autofirm")
