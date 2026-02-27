---
name: proofer
description: >
  Editorial reviewer for documents, code, and content. Use when you need to
  proofread, review, or critique written material before publishing.
allowed-tools: "Bash(guppi-proofer:*)"
version: "0.1.0"
author: "Sam Dengler"
license: "MIT"
---

# Proofer — editorial reviewer

**STATUS: DRAFT — not yet implemented. See docs/design/ for the plan.**

Review and critique documents, code, and content before they go out. Think red-pen markup — grammar, clarity, tone, structure, and consistency.

## Planned Commands

### `guppi-proofer review <file>`

Review a file and provide editorial feedback.

## Skill Management

```bash
guppi-proofer skill install   # Register with guppi-cli
guppi-proofer skill show      # Display SKILL.md contents
```
