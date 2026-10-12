#!/usr/bin/env python3
"""A synthetic, stdlib-only example of fact-gating an AI-generated sports caption.

This file is a new demonstration written for public review, not an export of
the private Caption Automator 1000 implementation. It performs no network
requests, reads no photographs, and does not change metadata.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping


# Deliberately constrained output: an untrusted model cannot invent an action
# that will appear in a publishable caption through this demonstration.
ALLOWED_ACTIONS = {
    "pass": "passes to a teammate",
    "shot": "takes a shot",
    "defend": "defends during play",
}
EVIDENCE_FOR_AUTO_DRAFT = {"play_by_play", "readable_jersey"}


@dataclass(frozen=True)
class Result:
    frame_id: str
    status: str  # "ready", "review_required", or "human_owned"
    caption: str | None
    reasons: tuple[str, ...]


def _normalized(value: Any) -> str:
    return " ".join(str(value or "").casefold().split())


def assess_frame(
    frame: dict[str, Any],
    roster: list[dict[str, Any]],
    *,
    approved_edits: Mapping[str, str] | None = None,
    trusted_evidence: Mapping[str, list[str]] | None = None,
) -> Result:
    """Review structured AI candidates against trusted roster facts.

    A matching name alone is not enough for an automatic draft. The candidate
    also needs team and jersey consistency, usable evidence, and an approved
    action code. REVIEW records never produce a publishable caption.
    """
    frame_id = str(frame.get("id", "unnamed"))

    # An AI-supplied frame is *never* permitted to grant itself human approval.
    # The caller must pass separately maintained, photographer-controlled edits.
    # This demonstration models the precedence rule without editing metadata.
    edits = approved_edits or {}
    if frame_id in edits:
        human_text = str(edits[frame_id])
        if not human_text.strip():
            return Result(frame_id, "review_required", None,
                          ("human edit is empty",))
        return Result(frame_id, "human_owned", human_text,
                      ("human edit preserved",))

    observed = frame.get("observation") or {}
    name = _normalized(observed.get("player"))
    team = _normalized(observed.get("team"))
    jersey = str(observed.get("number", "")).strip()
    # Model-supplied evidence labels are untrusted and ignored. The caller
    # passes independent, verified source signals separately.
    evidence = set((trusted_evidence or {}).get(frame_id, ()))
    action_code = str(observed.get("action_code", "")).strip()

    reasons: list[str] = []
    if not name:
        reasons.append("missing player identity")
    if not team:
        reasons.append("missing team identity")
    if not jersey:
        reasons.append("missing jersey number")
    if not (evidence & EVIDENCE_FOR_AUTO_DRAFT):
        reasons.append("no reliable identity evidence")
    if action_code not in ALLOWED_ACTIONS:
        reasons.append("action not in approved vocabulary")

    named = [entry for entry in roster
             if _normalized(entry.get("name")) == name]
    if name and not named:
        reasons.append("player absent from trusted roster")

    matches = [entry for entry in named
               if _normalized(entry.get("team")) == team
               and str(entry.get("number", "")).strip() == jersey]
    if named and not matches:
        reasons.append("player, team and jersey do not agree")

    # Uniform numbers alone are not identities. When several names share
    # a number on the same team, even a model-suggested name needs review.
    same_number = [entry for entry in roster
                   if str(entry.get("number", "")).strip() == jersey
                   and (not team or _normalized(entry.get("team")) == team)]
    if jersey and len(same_number) > 1:
        reasons.append("jersey number does not uniquely identify a player")
    if len(matches) > 1:
        reasons.append("duplicate matching roster entries")

    if reasons:
        return Result(frame_id, "review_required", None, tuple(dict.fromkeys(reasons)))

    verified = matches[0]  # canonical spelling comes from the trusted roster
    caption = (
        f"{verified['name']} ({jersey}) of {verified['team']} "
        f"{ALLOWED_ACTIONS[action_code]}."
    )
    return Result(frame_id, "ready", caption, ())


def review_fixture(data: dict[str, Any]) -> list[Result]:
    """Run a fully local, synthetic scenario. No AI service is contacted."""
    if data.get("synthetic") is not True:
        raise ValueError("Only explicitly synthetic fixtures are accepted.")
    roster = data["roster"]
    approved_edits = data.get("approved_edits", {})
    trusted_evidence = data.get("trusted_evidence", {})
    return [assess_frame(frame, roster, approved_edits=approved_edits,
                         trusted_evidence=trusted_evidence)
            for frame in data["frames"]]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path,
                        help="Path to a synthetic JSON fixture")
    args = parser.parse_args()
    data = json.loads(args.fixture.read_text(encoding="utf-8"))
    for result in review_fixture(data):
        print(json.dumps(asdict(result), ensure_ascii=False))


if __name__ == "__main__":
    main()
