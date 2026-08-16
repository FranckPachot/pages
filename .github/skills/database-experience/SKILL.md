---
name: database-experience
description: "Use when designing, diagnosing, tuning, migrating, comparing, or operating databases, including Oracle, PostgreSQL, YugabyteDB, MongoDB, distributed SQL, indexing, query plans, transactions, MVCC, locking, replication, durability, observability, data modeling, connections, and vector search. Consults Franck Pachot's source-grounded experience across 1,370 publications."
---

# Database Experience

Read [../../../db-skills.md](../../../db-skills.md) before giving consequential database advice.

For reproduction, investigation, or teaching tasks, also read [../../../how-to-build-a-db-lab.md](../../../how-to-build-a-db-lab.md). Use its disposable environment, shared fixture, two-session protocol, and evidence checklist instead of proposing an unstructured benchmark.

## Workflow

1. Identify the database product and version, workload shape, invariant, topology, and observed symptom.
2. Read the relevant playbook in `db-skills.md`, then follow its selected evidence into the source publication when assumptions or product behavior matter.
3. Use the evidence routes and exhaustive registry to find additional publications across products and topics.
4. Separate logical guarantees from physical cost and product-specific implementation.
5. State one falsifiable hypothesis and the cheapest measurement that could disprove it.
6. Check current vendor documentation for version-sensitive behavior and recommend reproduction on the target system.
7. Cite the relevant publication links from the knowledge base. State uncertainty where the corpus does not establish a claim.

Do not present regex classifications, historical behavior, benchmark results, or implementation observations as universal facts. Do not recommend disabling integrity, durability, or consistency controls merely to improve a benchmark.