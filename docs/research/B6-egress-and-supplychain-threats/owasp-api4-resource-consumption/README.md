# API4:2023 Unrestricted Resource Consumption — OWASP API Security Top 10

## 1. Full citation

- **Title:** "API4:2023 — Unrestricted Resource Consumption," *OWASP API Security Top 10 (2023 edition)*
- **Author / Org:** OWASP Foundation, API Security Project
- **Year:** 2023
- **URL:** https://owasp.org/API-Security/editions/2023/en/0xa4-unrestricted-resource-consumption/

Note: this risk **replaced** the 2019 entry "API4:2019 Lack of Resources & Rate Limiting"; the underlying vulnerability is the same, broadened to cover *all* resource classes including paid third-party quotas.

## 2. Faithful structured summary

**Definition:** Satisfying an API request consumes resources (network, CPU, memory, storage). When an API fails to enforce limits on a client's consumption, an attacker can exhaust those resources → denial of service and/or runaway cost.

**Exhaustible resources enumerated:** network bandwidth, CPU cycles, memory allocation, storage capacity, **file descriptors**, **running processes**, and **third-party API quotas (paid services)** — e.g. SMS, email, biometric validation.

**Attack scenarios (from the spec):**
1. Repeatedly triggering a password-reset / SMS-verification endpoint, generating thousands of costly third-party SMS deliveries.
2. GraphQL batching — submitting many operations in a single request to bypass per-request rate limits and exhaust server memory.
3. Large cloud-storage downloads exceeding cache limits, causing unexpected cloud bandwidth charges.

**"How To Prevent" recommendations (load-bearing, exact phrasing):**
- Use containerization / serverless to constrain *"memory, CPU, number of restarts, file descriptors, and processes."*
- *"Define and enforce a maximum size of data on all incoming parameters and payloads."*
- *"Implement a limit on how often a client can interact with the API within a defined timeframe"* (rate limiting), fine-tuned **per endpoint** to business need.
- *"Limit/throttle how many times or how often a single API client/user can execute a single operation."*
- Validate query parameters that control the number of records in a response.
- *"Configure spending limits for all service providers/API integrations."*

## 3. Best parts to take → AutoFirm controls

- **This is the authoritative spec behind the gateway's throttling + validation duties.** AutoFirm's egress gateway is exactly the OWASP-API-validated PEP; API4 enumerates the precise controls it must enforce: payload-size caps, per-endpoint rate limits, per-operation throttling.
- **"Third-party API quotas" + "spending limits" is the cost-DoS row for an autonomous platform.** AutoFirm runs unattended; a buggy or adversarially-prompted agent loop can burn Anthropic/model spend or third-party quota without bound. The OWASP mandate to *"configure spending limits for all service providers/API integrations"* directly grounds a hard, per-session and per-platform spend/quota cap enforced at the gateway, with the out-of-band kill-switch as the backstop.
- **Per-session, per-operation throttling** maps onto the credential broker's per-session least-privilege scoping — each `claude` CLI session gets a bounded request budget, so one runaway session cannot starve the others (blast-radius containment).
- **"Constrain restarts, file descriptors, processes"** grounds running CLI sessions under containerized/cgroup limits, complementing the supervision-tree restart caps (see `erlang-otp-supervision-trees`) so a crash-loop can't exhaust host resources.
- **Fail-closed alignment:** when a session hits its resource/spend limit, AutoFirm refuses further egress for that session (fail closed) rather than proceeding — the house control, grounded by OWASP's deny-by-default posture.
