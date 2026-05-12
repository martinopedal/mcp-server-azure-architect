---
name: "docs-style"
description: "Documentation emoji policy, voice profile, and prose rules"
domain: "documentation, style, voice"
confidence: "high"
source: "directive (captured from news-fetcher voice profile + project style directive)"
---

## Context

All project documentation must follow a consistent voice profile and style ruleset. This skill captures the rules for every documentation change, including README.md, CHANGELOG.md, docs/, ADRs, PR templates, and agent-authored doc fragments.

## Emoji Policy

- **Only permitted:** `✅` and `❌`
- **Use case:** Status only (passed/failed, supported/unsupported, allowed/forbidden, present/absent in comparison tables)
- **Prohibited:** All other decorative emojis (🚀📦🎯🧠⚠️🔧📖🛡️🔒💡🎨✨⭐🔥, etc.)
- **Exempt:** Code blocks, shell output, .squad/ coordinator UI

## Voice Profile Rules

### Opening

- **Open directly.** State the point in the first sentence. No warm-up preamble.
- **Avoid:** "In today's world", "As we all know", "I'm excited to share", "This document covers", "In conclusion"
- **Avoid throwaway sections:** Skip "Overview" or "Introduction" sections that just restate the title.
- **Conclusion before reasoning.** Answer first, then explain why.
- **For product/feature docs:** Lead with what it does and why someone would use it.

### Body

- **Concrete examples.** Name specific tools, files, commands, error strings. Avoid abstractions when you can point at something real.
- **Pragmatic over theoretical.** Describe what works in practice over what reads well in a diagram.
- **Balance critique with context.** When recommending against something, acknowledge why the alternative exists before explaining the gap.
- **Active voice.** Named owner of the action. Avoid passive voice that hides accountability.
- **Vary paragraph length.** Mix one long paragraph, one short punchy line, one medium. Avoid 4-paragraph symmetry.

### Closers

- **End with a statement at least half the time.** Not every section needs a question.
- **Concrete next steps.** If you invite action, give a file path, command, or link, not "let me know your thoughts".

## Banned Phrases (Exhaustive)

Replace or remove (case-insensitive match):

| Phrase | Replace with |
|--------|--------------|
| `leverage`, `leveraging` | `use`, `using` |
| `utilize`, `utilizing` | `use`, `using` |
| `delve`, `dive into`, `deep dive` | `describe`, `explain` |
| `seamless`, `seamlessly` | Drop or describe what is smooth |
| `robust` | Drop or list what is handled |
| `streamlined` | Drop or describe what was simplified |
| `comprehensive` | Drop or list what is covered |
| `cutting-edge`, `state-of-the-art`, `transformative` | Drop |
| `unleash`, `unlock`, `empower`, `harness`, `paradigm` | Drop |
| `in today's landscape`, `in today's world`, `at the end of the day`, `it goes without saying` | Drop |
| `furthermore`, `moreover`, `additionally`, `on the other hand`, `in conclusion`, `to sum up`, `in fact` | Drop or replace with period and fresh sentence |
| `it's important to note that X` | Just `X.` |
| `let's dive in`, `let's explore`, `we will explore` | Drop |
| `feel free to`, `if you found this helpful`, `if this resonates` | Drop |
| `drive`, `driving` (as in "driving outcomes") | Describe what is moving |
| `journey` (career or product evolution) | Use concrete word: "career", "release history" |
| `game-changer` | Drop |
| **Heading: explanation** | Rewrite as a sentence |
| Tricolon openers: "Faster. Cheaper. Smarter." | Use a real opening sentence |
| Question-then-self-answer: "But what does this mean? Let's dive in." | If you ask, leave it open or answer with a position, not a transition |
| Forced sports/cooking/marathon analogies | Use concrete examples instead |

## Punctuation Rules

- **No em dashes (`—` U+2014).** Use period, comma, or colon.
- **No en dashes (`–` U+2013) as sentence separators.** En dashes in number ranges (2026–2027) or page ranges are fine.
- **No unicode arrows (`→`, `⇒`, `↗`).** Use `then`, `produces`, `becomes`, or `->` (code arrow) inside code spans.

## Examples

### ✓ Correct

```markdown
# Getting started with the server

The server exposes six native tools for Azure architects: alz_query_by_id, 
alz_query_list, pricing_lookup_sku, pricing_compare_skus, alz_scorecard, 
and health_check. Use it for named checklist queries and scorecard 
composition. For raw Azure APIs (Resource Graph, Advisor, Monitor), use 
azure-mcp directly.

Install via pip:
\`\`\`bash
pip install mcp-server-azure-architect
\`\`\`
```

### ✗ Incorrect

```markdown
# Getting Started With The Server

## Overview

In today's cloud landscape, architects need multiple tools to orchestrate 
their infrastructure. This document covers how to get started.

The server provides comprehensive native tools that seamlessly integrate 
with azure-mcp, unleashing powerful capabilities for architects.

Feel free to install the robust server via pip...
```

## Exempt Scopes

- Code comments (in src/, tests/, scripts/)
- Shell output and examples shown in documentation
- .squad/ coordinator UI and status tables
- .github/agents/ governance files
- Vendored content (data/alz-queries/)

## How to Apply

1. **When writing or rewriting docs:** Check each sentence against the banned phrases list.
2. **When reviewing PRs:** Skim for throwaway introductions, passive voice, and concrete examples.
3. **When editing existing docs:** Replace a phrase only if you're touching that section anyway. Don't do a wholesale sweep just for style.
4. **When in doubt:** Open the doc, read it aloud. If you hear marketing jargon or corporate tone, rewrite it.

## References

- Voice profile directive: `.squad/decisions/inbox/copilot-directive-20260512150500-voice-profile.md`
- Emoji policy directive: `.squad/decisions/inbox/copilot-directive-20260512150310-docs-style.md`
- Applied in PR: chore/docs-style-cleanup
