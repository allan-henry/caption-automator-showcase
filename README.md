# Caption Automator 1000: product and validation showcase

*A standalone demonstration using fictional athletes, fictional teams, and no photographs.*

## The problem

At a live sports assignment, getting images to editors quickly is only part of the job. Each published image needs correct player identification, event context, and structured caption metadata. A fluent but incorrect AI answer is worse than a clearly flagged image that needs attention.

I built Caption Automator 1000 around that problem: use event data and AI assistance to prepare captions, keep deterministic checks between model output and the publishing workflow, and leave final editorial judgment with the photographer.

The full working project remains private. **This is a newly written, AI-assisted, deliberately limited demonstration of one important product decision: when to accept an AI candidate and when to require human review.** It is not a copy of the full production application.

## What this demonstration shows

An upstream vision or language model might suggest a player, team, uniform number, action, and claimed evidence. The sample Python program treats that suggestion as *untrusted input*. Verified evidence signals and approved human edits arrive through separate caller-controlled maps; the program ignores any approval or evidence claims embedded in the model's observation.

| Product decision | What the code demonstrates |
| --- | --- |
| An athlete must be identifiable | Candidate name, team, and uniform number must agree with the trusted roster |
| Visual guesses are not enough | Identification needs a separately supplied, verified supporting signal, such as play-by-play or a readable jersey; the AI cannot authorize itself |
| Duplicate uniform numbers create ambiguity | A number shared by multiple roster members in the relevant scope causes a review flag |
| Plausible prose is not a verified fact | Only a small approved action vocabulary can appear in a ready caption |
| A human edit takes precedence | An independent, trusted `approved_edits` record overrides AI candidates; an AI candidate cannot grant itself approval |
| Uncertainty should be visible | The result is either `ready`, `review_required`, or `human_owned`, with reasons |

A `review_required` item never receives a publishable caption.

## Try it locally

Requires Python 3.10+ and only the standard library.

```bash
python3 caption_review_demo.py fixtures/synthetic_game.json
python3 -m unittest discover -s tests -v
```

The fixture intentionally includes five examples: a valid observation, a duplicate jersey number, an unsupported identity, a separately approved photographer caption, and an AI-supplied attempt to forge human approval. The fictional `trusted_evidence` map is separate from AI-proposed `observation.evidence`, which the validator ignores.

No service credentials, API calls, images, XMP files, or external data feeds are required.

## How the complete private product differs

The original Caption Automator work includes more components than this excerpt:

- A game-night workflow connected to image export and review.
- EXIF timestamps, editorial metadata, league-specific adapters, and live play context.
- Multimodal analysis and identity validation under editorial constraints.
- Caching and failure handling to avoid unnecessary repeated processing.
- Human acceptance before captions enter the onward editorial workflow.

**Not demonstrated here:** invoking a real vision model, authenticating the photo/frame ID, verifying the underlying play-by-play or OCR result actually corresponds to the player, writing IPTC/XMP metadata, transmitting images, or validating all language in a free-form caption. An integrating product must enforce those source and identity boundaries. Passing these unit tests does not establish production accuracy or compliance with a wire service's requirements.

## My role and product decisions

As the photographer and product owner, I defined the workflow, customer requirements, error cases, and acceptance criteria. I coordinated AI-assisted implementation and reviewed outputs against real editorial problems, especially false identities, unsafe assumptions, and unwanted changes to work a photographer had already edited.

I chose to combine model assistance with deterministic checks rather than allowing model confidence alone to control publication. That tradeoff improves the usefulness of automation while preserving accountability at the human decision point.

## Repository boundaries

Everything under `fixtures/` is invented. In this example, the outer frame identifier, `trusted_evidence` and `approved_edits` are provided by a trusted caller, not by the AI. A real system must authenticate that separation and bind the identifier to its actual media record. This demonstration contains no customer information, event images, live API credentials, proprietary newsroom templates, real athlete rosters, or copied production code.

This public-facing case study is intentionally narrow. The original repository and history remain private; details of the full system can be discussed in an authorized technical review.

**Publication:** This standalone showcase is public with the owner's authorization. The original Caption Automator 1000 source, private history, and operational configurations remain private. No open-source license is granted by this repository's visibility.
