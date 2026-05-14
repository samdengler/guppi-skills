# Paper

Analyze academic papers using the Feynman Technique.

**Status:** Experimental | **Version:** 0.1.0 | **Created:** 2026-03-09

## What it does

Paper takes an academic paper URL and produces a structured analysis using the Feynman Technique. The analysis breaks the paper down into plain-language explanations, identifies gaps, provides critical analysis, and includes a technical deep dive — all formatted as clean markdown. It also estimates reading time so you know how much time the analysis saves you versus reading the original.

When used as an agent skill (`/paper <url>`), Claude fetches the paper, runs the full analysis, and writes everything to a folder in your current directory. When used from the terminal, it gives you the raw prompt or converts an existing analysis to PDF.

## When to use it

- You found an interesting paper and want to understand it quickly
- You need a structured summary to share with your team
- You want to build a personal library of paper analyses
- You need a PDF-ready breakdown of a paper for offline reading

## Quick start

```bash
# As an agent skill — full end-to-end analysis
/paper https://arxiv.org/pdf/2509.07604

# Generate the analysis prompt (e.g., to paste into another LLM)
guppi-paper prompt https://arxiv.org/pdf/2509.07604

# Copy the prompt to clipboard
guppi-paper prompt https://arxiv.org/pdf/2509.07604 | pbcopy

# Convert a finished analysis to PDF
guppi-paper pdf agent-first-database-systems/agent-first-database-systems-analysis.md
```

## What to expect

When you invoke `/paper <url>` as an agent skill, it:

1. Fetches the paper (PDF via pymupdf, or HTML via WebFetch)
2. Derives a kebab-case folder name from the paper title
3. Creates an output directory in your current working directory
4. Saves the source material (PDF or markdown) into the folder
5. Runs a Feynman Technique analysis and writes it to `<slug>-analysis.md`
6. Converts the analysis to PDF (unless `--no-pdf` is passed)

The analysis includes reading time estimates, a plain-language explanation, gap identification, critical analysis, and a technical deep dive.

## Commands

### `guppi-paper prompt <url>`

Output the hydrated Feynman Technique analysis prompt for a paper URL. The prompt is ready to paste into any LLM or use in a pipeline.

**Arguments:**
- `url` — URL of the academic paper (e.g., `https://arxiv.org/pdf/2509.07604`)

```bash
guppi-paper prompt https://arxiv.org/pdf/2509.07604
guppi-paper prompt https://arxiv.org/pdf/2509.07604 | pbcopy
```

### `guppi-paper pdf <markdown-file>`

Convert a markdown analysis file to PDF using pandoc with XeLaTeX. Outputs the PDF path on success.

**Arguments:**
- `markdown-file` — path to the markdown analysis file to convert

```bash
guppi-paper pdf agent-first-database-systems/agent-first-database-systems-analysis.md
```

The PDF is written alongside the markdown file with the same name and a `.pdf` extension.

## Prerequisites

- Python 3.11+
- [guppi-cli](https://github.com/agent-skills/guppi-cli) (for `guppi skills install`)
- `pandoc` and `basictex` for PDF conversion (`brew install pandoc basictex`)
