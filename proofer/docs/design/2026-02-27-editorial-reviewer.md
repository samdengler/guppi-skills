# Proofer - Design Doc [DRAFT]

**Status**: DRAFT - capturing rough ideas, not ready for implementation

## Concept

"Proofer" — an editorial review skill for Claude Code. Red-pen your documents,
code, and content before they go out. Grammar, clarity, tone, structure, and
consistency.

Renamed from "pressman" which was originally about PDF/print production. The
editorial review concept is more useful. PDF generation may become a separate
skill or a subcommand.

## Origin

Came up during Matt's beer tasting project where we needed to preview and iterate
on HTML documents. The review/feedback loop was the valuable part — not the PDF
generation itself.

## Potential Commands

### `guppi-proofer review <file>`
Review a file and provide editorial feedback. Could handle:
- Markdown docs — grammar, clarity, structure
- Code — comments, naming, documentation quality
- READMEs — completeness, accuracy, tone
- Emails/messages — tone, professionalism

### `guppi-proofer check <file> [--style STYLE]`
Check against a style guide (e.g., AP, Chicago, informal, technical).

## Open Questions

- What review engine? LLM-based (Claude API), rule-based, or hybrid?
- Should it produce inline annotations or a summary report?
- Should it support custom style guides / house rules?
- Integration with clipper for copying reviewed content?
- Should the old pressman PDF/preview features live here or elsewhere?
