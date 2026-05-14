---
name: paper
description: >
  Analyze academic papers using the Feynman Technique.
  Use when you need to create a clear, structured explanation of an academic paper.
allowed-tools: "Bash(guppi-paper:*), Bash(curl:*), WebFetch, Read, Write"
version: "0.1.1"
author: "Sam Dengler"
license: "MIT"
---

# Paper — Academic paper analyzer

Analyzes academic papers using the Feynman Technique, producing structured markdown explanations with reading time estimates, simplified explanations, critical analysis, and technical deep dives.

## Skill Workflow

When invoked as `/paper <url>`, follow these steps:

1. **Parse arguments**: Extract the paper source (URL or local file path) from `$ARGUMENTS`. Check for a `--no-pdf` flag (if present, skip step 7).

2. **Fetch the paper**:
   - **Local file** (path exists on disk): If PDF, extract text with `guppi-paper prompt <path>` (uses pymupdf). If text/markdown, read directly. Skip download.
   - **PDF URL** (ends in `.pdf`, contains `/pdf/`, or is a known PDF-serving pattern like arxiv.org/pdf/): Download with `curl -sL -o /tmp/<id>.pdf <url>`, then extract text with `guppi-paper prompt /tmp/<id>.pdf` and use the output.
   - **HTML URL**: Use `WebFetch` to retrieve and convert the content to markdown.
   - **Fallback**: If `WebFetch` returns binary/garbage content, the URL is likely a PDF — fall back to the curl + guppi-paper prompt approach.

3. **Derive folder name**: From the paper title, create a descriptive kebab-case slug (e.g., `agent-first-database-systems`). Do NOT use the arxiv ID or URL path — use the actual paper title.

4. **Create output directory**: Create the folder in the current working directory.

5. **Save source material**: Save the original content into the output directory:
   - **Local file**: Copy the file to `<slug>/<slug>.<ext>`
   - **PDF source**: Copy the downloaded PDF to `<slug>/<slug>.pdf`
   - **HTML source**: Write the markdown conversion to `<slug>/<slug>-source.md`

6. **Run the analysis**: Analyze the paper following the Feynman Technique instructions below. Write the result to `<slug>/<slug>-analysis.md`.

7. **PDF conversion** (unless `--no-pdf` flag): Run `guppi-paper pdf <path-to-analysis-markdown>` to convert the analysis to PDF.

## Feynman Technique Analysis Instructions

Analyze the paper systematically through these steps:

### Reading Time Estimate
Estimate reading time based on word count, page length, subject complexity, number of figures/tables/equations, and density of mathematical content.

### Step 1: Identify the Core Concept
Explain the core concept as if teaching someone with no background in the field. Use simple language, avoid jargon. What problem is being solved and why does it matter?

### Step 2: Teach It Simply
Explain the main contribution and methodology as if teaching an intelligent 12-year-old:
- The key innovation or finding
- How the authors achieved their results
- The experimental setup or theoretical framework

Use analogies and real-world examples.

### Step 3: Identify Gaps
- What assumptions aren't fully explained?
- Which technical details are glossed over?
- What background knowledge is assumed?
- Are there logical jumps in the argumentation?
- What questions remain unanswered?

### Step 4: Simplify and Reorganize
1. One-paragraph executive summary (max 100 words)
2. Three key takeaways in bullet points
3. One simple diagram description
4. An analogy that captures the essence
5. The "so what?" — real-world significance

### Critical Analysis
- Strengths (2-3 points)
- Weaknesses or limitations (2-3 points)
- Relation to the broader field
- Follow-up questions or research directions

### Technical Deep Dive
- Key equations or algorithms (simplified)
- Critical experimental results and meaning
- Statistical significance and validation methods
- Robustness of conclusions given the evidence

## Output Format

Structure the response with clear markdown headers. Include:
- Paper title and original URL at the top
- A "Reading Time Analysis" section showing estimated time for the original paper, this analysis, and time savings
- Prioritize clarity over completeness

## CLI Commands

### `guppi-paper prompt <source>`

Output the hydrated analysis prompt to stdout. Accepts a URL or local file path.

```bash
guppi-paper prompt https://arxiv.org/pdf/2509.07604
guppi-paper prompt ./paper.pdf
guppi-paper prompt https://arxiv.org/pdf/2509.07604 | pbcopy
```

### `guppi-paper pdf <markdown-file>`

Convert a markdown analysis file to PDF via pandoc.

```bash
guppi-paper pdf agent-first-database-systems-analysis.md
```

## Skill Management

```bash
guppi-paper skill install   # Register with guppi-cli
guppi-paper skill show      # Display SKILL.md contents
```
