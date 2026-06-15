# SUMMARY — NIST SP 800-204: Security Strategies for Microservices-based Application Systems

## Full citation
- **Title:** Security Strategies for Microservices-based Application Systems.
- **Author:** Ramaswamy Chandramouli (NIST).
- **Year:** August 2019.
- **Venue/Publisher:** NIST Special Publication 800-204 (final).
- **URL/DOI:** https://csrc.nist.gov/pubs/sp/800/204/final · PDF: https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-204.pdf
- **Series context (May 2023):** expanded to four publications: 800-204 (strategies), 800-204A (service-mesh authn/authz), 800-204B (attribute-based access for service mesh), 800-204C (zero-trust microservices).

## Questions informed
- **L1.A8.1** External-tool/API integration patterns & untrusted-input handling (API gateway, mTLS, throttling).
- Supporting for **L1.A8.3** (least-privilege service-to-service auth).

## GRADE tier
**High.** Official U.S. government standard by a recognized authority; normative-authoritative.

## Key claims (with locators)
1. **Core feature set (abstract):** "authentication and access management, service discovery, secure communication protocols, security monitoring, availability/resiliency (e.g., circuit breakers), load balancing and throttling, integrity assurance during induction of new services, and session persistence."
2. **API gateway as a dedicated security component:** SP 800-204 analyzes the API gateway and service mesh as the frameworks for enforcing core security features — the gateway is the centralized ingress/policy-enforcement point (authentication, rate limiting, request validation, TLS termination).
3. **Zero-trust integration (per the series):** enforce least privilege; secure service-to-service comms via strong (mutual) authentication; use secure API gateways for defense-in-depth. SP 800-204A/B position the service mesh for transport security via mTLS, propagation of workload identity, and fine-grained authorization.
4. **Throttling / circuit breakers** are first-class availability+security controls (back-pressure against abusive/malicious load).

## Up/down-rate reasoning
- Up-rated: official standard, authoritative author, multi-part series (204A/B/C) adds depth.
- Indirectness: written for microservices, not LLM-agent platforms — applied to AutoFirm as the gateway/mesh blueprint, a direct fit (the integration layer IS a gateway).

## Reproducibility note
Abstract feature list on the CSRC final page; the gateway/service-mesh + mTLS + least-privilege through-line spans 800-204/204A/204B/204C. Cite the specific sub-document for any mTLS/ABAC detail.
