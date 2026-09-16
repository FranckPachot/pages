# Publication reviews

This directory contains update notes for old publications. The original article and
its archived snapshot stay unchanged. A review answers one question: **what, if
anything, is different in a named current version?**

## Review states

- `queued`: selected for review; no current-behavior claim has been made.
- `researching`: documentation or a reproduction is in progress.
- `verified-no-change`: the reviewed claim still behaves as described.
- `verified-changed`: current behavior differs from the publication.
- `blocked`: the claim cannot currently be tested; the reason is recorded.

Only notes in a `verified-*` state are ready to copy into a publication manually.

## Evidence rules

1. Link to the published article and its immutable local snapshot.
2. Quote or summarize only the narrow claim being reviewed.
3. Record the original product version. Use `not stated` when it cannot be
   established from the article; do not infer a version from its publication date.
4. Name the exact reviewed version, edition, topology, and relevant settings.
5. Separate current documentation from observed behavior.
6. For a behavioral claim, preserve the commands, version output, and decisive
   result. Pin container images or record the resolved digest.
7. Say `not tested` or use `blocked` when evidence is incomplete.

## Note format

Create one Markdown file per publication under the relevant database directory:

```markdown
---
title: "Review: <publication title>"
article_url: <canonical URL>
archive_path: <repository-relative snapshot path>
published: YYYY-MM-DD
reviewed: YYYY-MM-DD
status: queued
original_version: "not stated"
reviewed_version: "not tested"
---

# <publication title>

## Update note

> This article described <behavior> in <original version>. In <reviewed version>,
> <what changed or what remains true>. I verified <test>, and observed <result>.

## Claim reviewed

<The narrow, version-sensitive statement from the article.>

## What changed

<Documented difference, or "No change found for this claim.">

## Verification

**Question:**

**Hypothesis:**

**Environment:**

**Commands:**

```text
<reproduction commands>
```

**Observed result:**

## Sources

- [Current product documentation](<URL>)
```

The blockquote is the short text intended for optional manual publication. The
sections below it retain the evidence and uncertainty behind that text.
