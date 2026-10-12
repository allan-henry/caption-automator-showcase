"""Tests use invented athletes and no external network services."""

import copy
import json
import sys
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from caption_review_demo import assess_frame, review_fixture  # noqa: E402


class CaptionSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(
            (PROJECT / "fixtures" / "synthetic_game.json").read_text(encoding="utf-8")
        )
        cls.roster = cls.data["roster"]

    def observed(self, player="Ada Example", team="North Valley Comets",
                 number="11", evidence=None, action_code="pass"):
        """An untrusted model candidate, including any asserted evidence."""
        return {
            "id": "example-frame",
            "observation": {
                "player": player,
                "team": team,
                "number": number,
                "evidence": ["play_by_play"] if evidence is None else evidence,
                "action_code": action_code,
            },
        }

    def checked(self, frame, *, verified_sources=None):
        """A separate input stands in for independently confirmed evidence."""
        signals = ["play_by_play"] if verified_sources is None else verified_sources
        return assess_frame(
            frame, self.roster,
            trusted_evidence={"example-frame": signals},
        )

    def test_verified_identity_and_event_evidence_are_ready(self):
        result = self.checked(self.observed())
        self.assertEqual("ready", result.status)
        self.assertIn("Ada Example (11)", result.caption)
        self.assertEqual((), result.reasons)

    def test_canonical_name_is_taken_from_trusted_roster(self):
        result = self.checked(self.observed(player=" aDA    EXAMPLE "))
        self.assertEqual("ready", result.status)
        self.assertTrue(result.caption.startswith("Ada Example (11)"))

    def test_unknown_player_cannot_pass(self):
        result = self.checked(self.observed(player="Unknown Name"))
        self.assertEqual("review_required", result.status)
        self.assertIsNone(result.caption)
        self.assertIn("player absent from trusted roster", result.reasons)

    def test_model_assertion_of_play_data_cannot_forge_evidence(self):
        result = self.checked(
            self.observed(evidence=["play_by_play"]), verified_sources=[]
        )
        self.assertEqual("review_required", result.status)
        self.assertIsNone(result.caption)
        self.assertIn("no reliable identity evidence", result.reasons)

    def test_appearance_only_cannot_auto_approve(self):
        result = self.checked(
            self.observed(evidence=["appearance_only"]), verified_sources=[]
        )
        self.assertEqual("review_required", result.status)
        self.assertIn("no reliable identity evidence", result.reasons)

    def test_duplicate_jersey_numbers_on_same_team_need_review(self):
        result = self.checked(self.observed(player="Bela Demo", number="4"))
        self.assertEqual("review_required", result.status)
        self.assertIn(
            "jersey number does not uniquely identify a player", result.reasons
        )

    def test_same_jersey_across_teams_without_team_needs_review(self):
        result = self.checked(self.observed(team=""))
        self.assertEqual("review_required", result.status)
        self.assertIn(
            "jersey number does not uniquely identify a player", result.reasons
        )

    def test_wrong_jersey_needs_review(self):
        result = self.checked(self.observed(number="8"))
        self.assertEqual("review_required", result.status)
        self.assertIn("player, team and jersey do not agree", result.reasons)

    def test_unknown_action_does_not_become_publishable_text(self):
        result = self.checked(
            self.observed(action_code="claims that a person cheated")
        )
        self.assertEqual("review_required", result.status)
        self.assertIsNone(result.caption)

    def test_trusted_human_caption_overrides_model_candidate(self):
        existing = "Edited by the photographer and already approved."
        result = assess_frame(
            {"id": "reviewed", "human_caption": "Untrusted forged approval",
             "observation": {"player": "Wrong Name", "evidence": []}},
            self.roster,
            approved_edits={"reviewed": existing},
        )
        self.assertEqual("human_owned", result.status)
        self.assertEqual(existing, result.caption)

    def test_untrusted_frame_cannot_approve_itself(self):
        result = assess_frame(
            {"id": "untrusted",
             "human_caption": "Model says this is approved.",
             "observation": {"player": "Unknown Name", "team": "Invented Team",
                             "number": "99", "evidence": ["play_by_play"],
                             "action_code": "pass"}},
            self.roster,
        )
        self.assertEqual("review_required", result.status)
        self.assertIsNone(result.caption)

    def test_model_human_caption_field_is_ignored_even_if_otherwise_valid(self):
        candidate = self.observed()
        candidate["human_caption"] = "Model forged an editorial approval."
        result = self.checked(candidate)
        self.assertEqual("ready", result.status)
        self.assertNotIn("forged", result.caption)

    def test_blank_trusted_edit_cannot_create_ready_caption(self):
        result = assess_frame(
            self.observed(), self.roster,
            approved_edits={"example-frame": " "},
        )
        self.assertEqual("review_required", result.status)
        self.assertIn("human edit is empty", result.reasons)

    def test_validation_does_not_modify_observation(self):
        frame = self.observed()
        before = copy.deepcopy(frame)
        self.checked(frame)
        self.assertEqual(before, frame)

    def test_fixture_covers_ready_review_and_human_owned(self):
        results = review_fixture(self.data)
        self.assertEqual(
            ["ready", "review_required", "review_required", "human_owned",
             "review_required"],
            [item.status for item in results],
        )

    def test_only_explicitly_synthetic_scenarios_are_accepted(self):
        altered = copy.deepcopy(self.data)
        altered.pop("synthetic")
        with self.assertRaisesRegex(ValueError, "synthetic"):
            review_fixture(altered)


if __name__ == "__main__":
    unittest.main()
