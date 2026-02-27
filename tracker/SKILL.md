---
name: tracker
description: >
  Cross-project task and idea tracker built on beads. Use when you need to
  capture ideas, tasks, reading lists, or track async work across projects.
allowed-tools: "Bash(guppi-tracker:*)"
version: "0.1.0"
author: "Sam Dengler"
license: "MIT"
---

# Tracker — cross-project task and idea tracker

Track ideas, tasks, reading lists, and async work items in a single place that works across projects. Built on beads for git-backed persistence and agent-friendly querying.

## Commands

### `guppi-tracker add <title>`

Add a new item to track.

## Examples

```bash
guppi-tracker add "Read the beads source for tag support"
guppi-tracker add "Try building a Chrome extension with Plasmo"
```

## Skill Management

```bash
guppi-tracker skill install   # Register with guppi-cli
guppi-tracker skill show      # Display SKILL.md contents
```
