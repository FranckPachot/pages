# Achieving Precise Clock Synchronization on AWS

- Original: [published 2024-12-03](https://www.yugabyte.com/blog/aws-clock-synchronization/)
- Review cutoff: 2026-03-06
- Status: `verified-changed`
- Evidence: documentation and release notes only; no EC2 or ClockBound test

## What was reviewed

The article demonstrates AWS Time Sync Service, PTP hardware clock error bounds, ClockBound, and YugabyteDB integration in the YugabyteDB 2.23.1 period.

## What changed

The mechanism remains the same, but product maturity changed. YugabyteDB release notes identify ClockBound integration as generally available in 2025.2.2. It still depends on supported AWS instances and correct host time-service configuration.

## Evidence

- [YugabyteDB 2025.2 release notes](https://docs.yugabyte.com/stable/releases/ybdb-releases/v2025.2/)
- [YugabyteDB time synchronization](https://docs.yugabyte.com/stable/architecture/transactions/distributed-txns/#time-synchronization)
- [AWS ClockBound](https://github.com/aws/clock-bound)

## Companion update

The article demonstrated ClockBound integration during the YugabyteDB 2.23.1 period. That integration reached GA in YugabyteDB 2025.2.2, while the underlying model remains the same: combine a precise clock with a defensible error bound. Availability still depends on supported EC2 hardware and correct PTP, PHC, Chrony, and ClockBound configuration; this review did not reproduce the AWS setup.